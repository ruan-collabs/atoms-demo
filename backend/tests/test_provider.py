"""Provider request-contract tests: no live API or real credentials."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch
import httpx
import pytest
from app.services.provider import completion,ProviderError

config=SimpleNamespace(provider='deepseek',base_url='https://api.deepseek.com',model='deepseek-flash')

def response_client(response,captured):
    class Client:
        def __init__(self,**kwargs):captured['options']=kwargs
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kwargs):captured.update(url=url,**kwargs);return response
    return Client

def test_deepseek_official_request_and_content_only(monkeypatch):
    captured={};response=httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'result','reasoning_content':'not returned'}}]})
    monkeypatch.setattr(httpx,'AsyncClient',response_client(response,captured))
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
        assert asyncio.run(completion(config,'test-only-credential',[{'role':'user','content':'hello'}]))=='result'
    assert captured['url']=='https://8.8.8.8/chat/completions'
    assert captured['headers']['Host']=='api.deepseek.com'
    assert captured['extensions']['sni_hostname']=='api.deepseek.com'
    assert captured['json']['thinking']=={'type':'disabled'}
    assert captured['json']['stream'] is False
    assert not captured['options']['trust_env'] and not captured['options']['follow_redirects']

@pytest.mark.parametrize('code,category',[(400,'request'),(401,'auth'),(402,'balance'),(403,'auth'),(429,'rate_limit'),(503,'upstream'),(302,'destination')])
def test_deepseek_errors_do_not_echo_raw_payload(monkeypatch,code,category):
    monkeypatch.setattr(httpx,'AsyncClient',response_client(httpx.Response(code,text='private upstream details'),{}))
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
        with pytest.raises(ProviderError) as e:asyncio.run(completion(config,'fixture-only-key',[]))
    assert e.value.category==category and 'private upstream' not in str(e.value)

@pytest.mark.parametrize('payload',[{},[],{'choices':[]},{'choices':[{'message':None}]},{'choices':[{'finish_reason':'length','message':{'content':'partial'}}]}])
def test_malformed_or_truncated_response_rejected(monkeypatch,payload):
    monkeypatch.setattr(httpx,'AsyncClient',response_client(httpx.Response(200,json=payload),{}))
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
        with pytest.raises(ProviderError):asyncio.run(completion(config,'fixture-only-key',[]))
