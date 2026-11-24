import asyncio
import json
from unittest.mock import patch
import httpx
import pytest
from app.services.provider import stream_completion, ProviderError
from test_provider import config


def mock_stream(monkeypatch, lines, captured):
    class Response:
        status_code=200
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def aiter_lines(self):
            for line in lines: yield line
    class Client:
        def __init__(self,**options): captured['options']=options
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        def stream(self,*args,**kwargs): captured['request']=kwargs;return Response()
    monkeypatch.setattr(httpx,'AsyncClient',Client)


def frames(values,finish='stop',done=True):
    result=['data: '+json.dumps({'choices':[{'delta':{'content':v,'reasoning_content':'never expose'},'finish_reason':None}]}) for v in values]
    result.append('data: '+json.dumps({'choices':[{'delta':{},'finish_reason':finish}]}))
    if done:result.append('data: [DONE]')
    return result


def run_stream():
    output=[]
    async def emit(text):output.append(text)
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
        value=asyncio.run(stream_completion(config,'fixture-only-key',[],emit))
    return value,output


def test_sse_real_content_no_reasoning_and_pinned_transport(monkeypatch):
    captured={};text='<html>'+('hello world '*100)+'</html>'
    mock_stream(monkeypatch,frames([text[:700],text[700:]]),captured)
    value,output=run_stream()
    assert value==text and ''.join(output)==text and len(output)>=2
    assert captured['request']['json']['stream'] is True
    assert captured['request']['extensions']['sni_hostname']=='api.deepseek.com'
    assert not captured['options']['trust_env']


@pytest.mark.parametrize('finish,done',[('length',True),('stop',False)])
def test_incomplete_output_never_success(monkeypatch,finish,done):
    mock_stream(monkeypatch,frames(['partial'],finish,done),{})
    with pytest.raises(ProviderError):run_stream()


def test_key_across_chunks_not_emitted(monkeypatch):
    mock_stream(monkeypatch,frames(['safe '*150+'fixture-only-','key']),{})
    emitted=[]
    async def emit(text):emitted.append(text)
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
        with pytest.raises(ProviderError) as error:
            asyncio.run(stream_completion(config,'fixture-only-key',[],emit))
    assert error.value.category=='leak'
    assert 'fixture-only' not in ''.join(emitted)


def test_task_css_identifier_not_key(monkeypatch):
    text='<!doctype html><html><body class="task-item"><style>.task-done {color:red}</style></body></html>'
    mock_stream(monkeypatch,frames([text]),{})
    assert run_stream()[0]==text


def test_standalone_key_prefix_still_blocked(monkeypatch):
    mock_stream(monkeypatch,frames(['<p>sk-','unexpectedsecret</p>']),{})
    with pytest.raises(ProviderError) as error:run_stream()
    assert error.value.category=='leak'


def test_extract_single_html_from_explanation():
    from app.services.artifacts import parse_output
    html='<!doctype html><html><head></head><body></body></html>'
    assert parse_output('Explanation\n```html\n'+html+'\n```')==html
    with pytest.raises(ProviderError):parse_output(html+html)
