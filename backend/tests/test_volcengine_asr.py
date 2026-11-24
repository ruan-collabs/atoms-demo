import asyncio
import gzip
import json
import struct
import pytest
from app.config import settings
from app.services import volcengine_asr as asr

def response(text,final=False):
    payload=gzip.compress(json.dumps({'result':{'text':text}}).encode())
    return bytes((0x11,0x93 if final else 0x91,0x11,0))+struct.pack('>iI',-1 if final else 1,len(payload))+payload

def test_protocol_packet_and_result_bounds():
    p=asr.request_packet(b'abc',audio=True,last=True)
    assert p[:4]==bytes((0x11,0x22,0x01,0)) and gzip.decompress(p[8:])==b'abc'
    assert asr.parse_response(response('测试'))==('测试',False)
    assert asr.parse_response(response('测试结束',True))==('测试结束',True)
    for packet in [b'bad',response('x'*4001),bytes((0x11,0xf0,0x10,0))+bytes(8),response('ok')[:-1]]:
        with pytest.raises(asr.ASRProtocolError):asr.parse_response(packet)
    payload=gzip.compress(b'x'*100001)
    with pytest.raises(asr.ASRProtocolError):asr.parse_response(bytes((0x11,0x90,0x11,0))+struct.pack('>I',len(payload))+payload)

def test_volc_status_exact_config(client,monkeypatch):
    monkeypatch.setattr(settings,'voice_provider','volcengine');monkeypatch.setattr(settings,'voice_enabled',True)
    monkeypatch.setattr(settings,'volc_asr_api_key','fixture-not-real');monkeypatch.setattr(settings,'volc_asr_resource_id','invalid')
    assert client.get('/api/voice/status').json()['enabled'] is False
    monkeypatch.setattr(settings,'volc_asr_resource_id','volc.seedasr.sauc.duration')
    data=client.get('/api/voice/status').json()
    assert data['enabled'] and data['provider']=='pipecat-volcengine' and 'fixture-not-real' not in json.dumps(data)

def test_fixed_destination_rejects_redirect_and_private_dns(monkeypatch):
    marker=RuntimeError('redirect fixture')
    assert asr.NoRedirectConnect.process_redirect(None,marker) is marker
    monkeypatch.setattr(asr.socket,'getaddrinfo',lambda *args,**kwargs:[(2,1,6,'',('127.0.0.1',443))])
    with pytest.raises(asr.ASRProtocolError):asyncio.run(asr.public_ip())


def test_upstream_error_never_echoed(client,monkeypatch):
    from app.services import voice
    class RejectedSocket:
        closed=False
        async def send(self,p):pass
        async def close(self):self.closed=True
        def __aiter__(self):return self
        async def __anext__(self):
            raise RuntimeError('SECRET-UPSTREAM-FIXTURE')
    socket=RejectedSocket()
    async def factory(*args,**kwargs):return socket
    async def ip():return '8.8.8.8'
    monkeypatch.setattr(asr,'public_ip',ip)
    monkeypatch.setattr(voice,'VolcengineSTTProcessor',lambda:asr.VolcengineSTTProcessor(connection_factory=factory))
    monkeypatch.setattr(settings,'voice_provider','volcengine');monkeypatch.setattr(settings,'voice_enabled',True)
    monkeypatch.setattr(settings,'volc_asr_api_key','fixture-not-real');monkeypatch.setattr(settings,'volc_asr_resource_id','volc.seedasr.sauc.duration')
    monkeypatch.setattr(settings,'dev_mock_auth',True)
    client.post('/api/dev/mock-login',json={'account':'alice'})
    with client.websocket_connect('/api/voice/ws',headers={'Origin':settings.public_origin}) as ws:
        assert ws.receive_json()['type']=='ready'
        data=ws.receive_json()
        assert data['type']=='error' and 'SECRET-UPSTREAM-FIXTURE' not in json.dumps(data)
    assert socket.closed


def test_volc_pipecat_stream_and_finalize(client,monkeypatch):
    from app.services import voice
    from app.api.voice import active_sessions
    sockets=[];seen={}
    class FakeSocket:
        def __init__(self):self.queue=asyncio.Queue();self.sent=[];self.closed=False;sockets.append(self)
        async def send(self,p):
            self.sent.append(p)
            if p[1]>>4==2:await self.queue.put(response('实时文字',bool(p[1]&2)))
        async def close(self):self.closed=True
        def __aiter__(self):return self
        async def __anext__(self):return await self.queue.get()
    async def factory(url,**kwargs):seen.update(url=url,**kwargs);return FakeSocket()
    async def ip():return '8.8.8.8'
    monkeypatch.setattr(asr,'public_ip',ip)
    monkeypatch.setattr(voice,'VolcengineSTTProcessor',lambda:asr.VolcengineSTTProcessor(connection_factory=factory))
    monkeypatch.setattr(settings,'voice_provider','volcengine');monkeypatch.setattr(settings,'voice_enabled',True)
    monkeypatch.setattr(settings,'volc_asr_api_key','fixture-not-real');monkeypatch.setattr(settings,'volc_asr_resource_id','volc.seedasr.sauc.duration')
    monkeypatch.setattr(settings,'dev_mock_auth',True)
    assert client.post('/api/dev/mock-login',json={'account':'alice'}).status_code==200
    with client.websocket_connect('/api/voice/ws',headers={'Origin':settings.public_origin}) as ws:
        assert ws.receive_json()['type']=='ready'
        ws.send_bytes(bytes(6400));a=ws.receive_json()
        assert a['text']=='实时文字' and a['replace'] is True and not a['final']
        ws.send_text('{"type":"stop"}');b=ws.receive_json()
        assert b['text']=='实时文字' and b['final'] and b['replace']
        assert ws.receive_json()['type']=='done'
    assert not active_sessions and sockets[0].closed
    assert seen['url']==asr.URL and seen['proxy'] is None and seen['server_hostname']==asr.HOST and seen['host']=='8.8.8.8'
    assert 'X-Api-Key' in seen['additional_headers'] and 'X-Api-Access-Key' not in seen['additional_headers']
    assert json.loads(gzip.decompress(sockets[0].sent[0][8:]))['request']['result_type']=='full'
    assert sockets[0].sent[-1][1]==0x22
