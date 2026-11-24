"""Pinned public-IP HTTPS egress: no redirects, ambient proxies or arbitrary destinations."""
import asyncio
import json
import re
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit
import httpx
from app.config import settings

class ProviderError(Exception):
    def __init__(self,message,category='provider',*,finish_reason=None,http_status=None,received_bytes=0):
        super().__init__(message);self.category=category
        self.finish_reason=finish_reason if finish_reason in ('length','stop','content_filter','tool_calls') else None
        self.http_status=http_status;self.received_bytes=received_bytes

def resolve_target(base_url):
    try:
        parts=urlsplit(base_url)
        if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.port not in (None,443):
            raise ValueError()
        origin='https://'+parts.netloc
        if origin not in settings.allowed_model_origins:raise ProviderError('服务目标未加入允许名单','destination')
        records=socket.getaddrinfo(parts.hostname,443,type=socket.SOCK_STREAM)
        addresses=list(dict.fromkeys(r[4][0] for r in records))
        if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
            raise ProviderError('拒绝内网、回环或非公开网络目标','destination')
        ip=addresses[0]
        authority=f'[{ip}]' if ':' in ip else ip
        path=parts.path.rstrip('/')+'/chat/completions'
        return urlunsplit(('https',authority,path,'','')),parts.hostname
    except ProviderError:raise
    except (OSError,ValueError):raise ProviderError('目标地址或DNS解析无效','destination') from None

async def completion(config,key,messages,timeout=45,max_tokens=8192):
    url,hostname=await asyncio.to_thread(resolve_target,config.base_url)
    try:
        payload={'model':config.model,'messages':messages,'max_tokens':max_tokens,'stream':False}
        if config.provider=='deepseek':
            parts=urlsplit(config.base_url)
            if parts.hostname!='api.deepseek.com' or parts.path.rstrip('/') not in ('','/v1'):
                raise ProviderError('DeepSeek只支持官方标准API地址','destination')
            payload['thinking']={'type':'disabled'}
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout,connect=10),follow_redirects=False,trust_env=False) as client:
            # Host+TLS SNI keep certificate verification for original allowed hostname;
            # actual TCP destination is the public IP just checked above, pinning DNS.
            response=await client.post(url,headers={'Host':hostname,'Authorization':'Bearer '+key,'Content-Type':'application/json'},
                extensions={'sni_hostname':hostname},json=payload)
        code=response.status_code
        check_status(code)
        if len(response.content)>2_000_000:raise ProviderError('上游产物超过大小限制','artifact')
        data=response.json()
        if not isinstance(data,dict) or not isinstance(data.get('choices'),list) or not data['choices'] or not isinstance(data['choices'][0],dict):
            raise ProviderError('上游响应结构异常','network')
        choice=data['choices'][0]
        if choice.get('finish_reason') not in (None,'stop'):
            reason=choice.get('finish_reason')
            raise ProviderError('模型输出达到长度上限，未保存不完整候选' if reason=='length' else '模型拒绝或中断输出，未保存候选','truncated' if reason=='length' else 'refusal',finish_reason=reason)
        message=choice.get('message')
        if not isinstance(message,dict):raise ProviderError('上游响应结构异常','network')
        value=message.get('content')
        if not isinstance(value,str) or not value.strip():raise ProviderError('上游未返回有效生成文本','artifact')
        if key in value:raise ProviderError('产物疑似包含凭证，已阻止保存','leak')
        return value
    except ProviderError:raise
    except (httpx.ConnectError,httpx.ConnectTimeout,httpx.PoolTimeout):
        raise ProviderError('模型连接未建立，尚未发送生成请求','connect') from None
    except httpx.TimeoutException:raise ProviderError('模型请求超时；上游结果未知，不自动重复计费','timeout') from None
    except (httpx.HTTPError,ValueError,IndexError,KeyError):raise ProviderError('模型网络、TLS或响应结构异常','network') from None


def check_status(code):
    if code == 400: raise ProviderError('模型请求参数无效，请检查模型ID与接口格式', 'request')
    if code in (401, 403, 404): raise ProviderError('模型Key、权限或模型无效，请重新配置', 'auth')
    if code == 402: raise ProviderError('模型账户余额不足', 'balance')
    if code in (429,500,502,503,504):
        raise ProviderError(f'模型服务暂时不可用（HTTP {code}）','http_retry',http_status=code)
    if 300 <= code < 400: raise ProviderError('拒绝供应商重定向', 'destination')
    if code != 200: raise ProviderError(f'上游服务错误（HTTP {code}）', 'upstream')


async def stream_completion(config, key, messages, on_delta, timeout=60, max_tokens=8192):
    """Content-only SSE. Hold back enough text to catch credentials across chunks.

    Raw frames and reasoning are never sent to callers. No transport retry.
    """
    url, hostname = await asyncio.to_thread(resolve_target, config.base_url)
    payload = {'model': config.model, 'messages': messages, 'max_tokens': max_tokens, 'stream': True}
    if config.provider == 'deepseek':
        parts = urlsplit(config.base_url)
        if parts.hostname != 'api.deepseek.com' or parts.path.rstrip('/') not in ('', '/v1'):
            raise ProviderError('DeepSeek只支持官方标准API地址', 'destination')
        payload['thinking'] = {'type': 'disabled'}
    tail = ''
    full = ''
    finished = False
    done = False
    wire_bytes = 0
    # Generic API-key patterns are checked with a long suffix buffer as well.
    if len(key)>4096:raise ProviderError('模型凭证格式无效','auth')
    hold = max(512, len(key) + 16)
    leak_pattern = re.compile(r'(?<![A-Za-z0-9_-])(?:sk-|Bearer\s+)',re.I)

    boundary = ''
    async def emit(text, flush=False):
        nonlocal tail, boundary
        tail += text
        if (key and key in tail) or leak_pattern.search(boundary+tail,len(boundary)):
            raise ProviderError('产物疑似包含凭证，已阻止输出与保存', 'leak')
        count = len(tail) if flush else max(0, len(tail) - hold)
        if count:
            safe, tail = tail[:count], tail[count:]
            boundary=(boundary+safe)[-32:]
            await on_delta(safe)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=10), follow_redirects=False, trust_env=False) as client:
            async with client.stream('POST', url,
                headers={'Host': hostname, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
                extensions={'sni_hostname': hostname}, json=payload) as response:
                check_status(response.status_code)
                async for line in response.aiter_lines():
                    wire_bytes += len(line.encode())
                    if wire_bytes > 4_000_000 or len(line) > 131072:
                        raise ProviderError('上游流式响应超过限制', 'artifact')
                    if not line.startswith('data:'):
                        continue
                    raw = line[5:].strip()
                    if raw == '[DONE]':
                        done = True
                        break
                    data = json.loads(raw)
                    if not isinstance(data, dict) or data.get('error'):
                        raise ProviderError('上游流式响应异常', 'network')
                    choices = data.get('choices')
                    if choices == []: continue  # usage-only final frame
                    if not isinstance(choices, list) or len(choices) != 1:
                        raise ProviderError('上游流式响应结构异常', 'network')
                    choice = choices[0]
                    delta = choice.get('delta', {})
                    if not isinstance(delta, dict) or delta.get('refusal') or delta.get('tool_calls'):
                        raise ProviderError('模型未返回有效应用内容', 'refusal')
                    value = delta.get('content') or ''
                    if not isinstance(value, str): raise ProviderError('上游内容格式异常', 'network')
                    full += value
                    if len(full.encode()) > 1_000_000: raise ProviderError('产物超过大小限制', 'artifact')
                    await emit(value)
                    reason = choice.get('finish_reason')
                    if reason is not None:
                        if reason != 'stop':
                            raise ProviderError('模型输出达到长度上限，未保存不完整候选' if reason=='length' else '模型拒绝或中断输出，未保存候选', 'truncated' if reason=='length' else 'refusal',finish_reason=reason,received_bytes=len(full.encode()))
                        finished = True
        if not (finished and done and full.strip()):
            raise ProviderError('模型流中断；不自动重复计费请求', 'network')
        await emit('', flush=True)
        return full
    except ProviderError: raise
    except (httpx.ConnectError,httpx.ConnectTimeout,httpx.PoolTimeout):
        raise ProviderError('模型连接未建立，尚未发送生成请求','connect') from None
    except httpx.TimeoutException: raise ProviderError('模型请求超时；上游结果未知，不自动重复计费', 'timeout') from None
    except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError):
        raise ProviderError('模型网络、TLS或流式响应结构异常', 'network') from None
