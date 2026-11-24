"""Pinned public-IP HTTPS egress: no redirects, ambient proxies or arbitrary destinations."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit
import httpx
from app.config import settings

class ProviderError(Exception):
    def __init__(self,message,category='provider'):
        super().__init__(message);self.category=category

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
        if code==400:raise ProviderError('模型请求参数无效，请检查模型ID与接口格式','request')
        if code in (401,403):raise ProviderError('模型Key或权限无效，请重新配置','auth')
        if code==402:raise ProviderError('模型账户余额不足','balance')
        if code==404:raise ProviderError('模型或接口不存在，请重新配置','auth')
        if code==429:raise ProviderError('模型请求受限，请稍后手动重试','rate_limit')
        if 300<=code<400:raise ProviderError('拒绝供应商重定向','destination')
        if code!=200:raise ProviderError(f'上游服务错误（HTTP {code}）','upstream')
        if len(response.content)>2_000_000:raise ProviderError('上游产物超过大小限制','artifact')
        data=response.json()
        if not isinstance(data,dict) or not isinstance(data.get('choices'),list) or not data['choices'] or not isinstance(data['choices'][0],dict):
            raise ProviderError('上游响应结构异常','network')
        choice=data['choices'][0]
        if choice.get('finish_reason') not in (None,'stop'):
            raise ProviderError('模型输出被截断、拒绝或中断，未保存候选','artifact')
        message=choice.get('message')
        if not isinstance(message,dict):raise ProviderError('上游响应结构异常','network')
        value=message.get('content')
        if not isinstance(value,str) or not value.strip():raise ProviderError('上游未返回有效生成文本','artifact')
        if key in value:raise ProviderError('产物疑似包含凭证，已阻止保存','leak')
        return value
    except ProviderError:raise
    except httpx.TimeoutException:raise ProviderError('模型请求超时；不自动重复计费请求','timeout') from None
    except (httpx.HTTPError,ValueError,IndexError,KeyError):raise ProviderError('模型网络、TLS或响应结构异常','network') from None
