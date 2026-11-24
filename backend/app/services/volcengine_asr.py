"""Volcengine ASR v3: fixed WSS destination, bounded binary protocol, full-result replacement.
No audio, credential, transcript or raw upstream error logging/persistence.
"""
import asyncio
import contextlib
import gzip
import ipaddress
import json
import logging
import socket
import ssl
import struct
import zlib
from dataclasses import dataclass
from websockets.asyncio.client import connect
from pipecat.frames.frames import (StartFrame, CancelFrame, EndFrame, Frame,
    InputAudioRawFrame, InterimTranscriptionFrame, TranscriptionFrame,
    ErrorFrame, VADUserStoppedSpeakingFrame)
from pipecat.processors.frame_processor import FrameProcessor
from app.config import settings

URL='wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async'
HOST='openspeech.bytedance.com'
MAX_RESULT=100_000
logging.getLogger('websockets').disabled=True

class ASRProtocolError(Exception):
    pass

@dataclass
class VoiceDoneFrame(Frame):
    pass

class NoRedirectConnect(connect):
    def process_redirect(self, exc):
        return exc

async def public_ip():
    records=await asyncio.to_thread(socket.getaddrinfo,HOST,443,type=socket.SOCK_STREAM)
    addresses=list(dict.fromkeys(r[4][0] for r in records))
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ASRProtocolError('unsafe destination')
    return addresses[0]

def request_packet(payload:bytes,audio=False,last=False):
    compressed=gzip.compress(payload)
    return bytes((0x11,0x22 if last else (0x20 if audio else 0x10),0x01 if audio else 0x11,0))+struct.pack('>I',len(compressed))+compressed

def parse_response(packet):
    if not isinstance(packet,bytes) or len(packet)<8 or len(packet)>MAX_RESULT:
        raise ASRProtocolError('invalid packet')
    if packet[0]>>4!=1:raise ASRProtocolError('invalid version')
    offset=(packet[0]&15)*4
    kind,flags=packet[1]>>4,packet[1]&15
    serialization,compression=packet[2]>>4,packet[2]&15
    if offset<4 or offset>len(packet)-4 or compression not in (0,1):raise ASRProtocolError('invalid header')
    if kind==15:raise ASRProtocolError('upstream rejected')
    if kind!=9 or flags not in (0,1,2,3) or serialization!=1:raise ASRProtocolError('unexpected type')
    if flags&1:offset+=4
    if offset+4>len(packet):raise ASRProtocolError('missing size')
    size=struct.unpack_from('>I',packet,offset)[0];offset+=4
    if size!=len(packet)-offset:raise ASRProtocolError('invalid size')
    payload=packet[offset:]
    if compression:
        d=zlib.decompressobj(16+zlib.MAX_WBITS)
        try:payload=d.decompress(payload,MAX_RESULT+1)
        except zlib.error:raise ASRProtocolError('invalid compression') from None
        if len(payload)>MAX_RESULT or not d.eof or d.unused_data:raise ASRProtocolError('compression limit')
    try:value=json.loads(payload)
    except (ValueError,UnicodeError):raise ASRProtocolError('invalid json') from None
    if not isinstance(value,dict) or value.get('code',20000000)!=20000000:raise ASRProtocolError('upstream rejected')
    result=value.get('result',{})
    if not isinstance(result,dict):raise ASRProtocolError('invalid result')
    text=result.get('text','')
    if not isinstance(text,str) or len(text)>4000:raise ASRProtocolError('transcript limit')
    return text,bool(flags&2)

class VolcengineSTTProcessor(FrameProcessor):
    def __init__(self,*,connection_factory=None):
        super().__init__()
        self.factory=connection_factory or NoRedirectConnect
        self.socket=None;self.reader=None;self.final=asyncio.Event();self.buffer=bytearray();self.stopped=False
        self.last_text='';self.last_final=False;self.failed=False

    async def _emit(self,text,final):
        if text==self.last_text and final==self.last_final:return
        self.last_text,self.last_final=text,final
        cls=TranscriptionFrame if final else InterimTranscriptionFrame
        await self.push_frame(cls(text,'','',result={'replace':True}))

    async def _read(self):
        try:
            async for packet in self.socket:
                text,final=parse_response(packet)
                await self._emit(text or (self.last_text if final else ''),final)
                if final:self.final.set();return
            if not self.stopped:raise ASRProtocolError('unexpected close')
        except asyncio.CancelledError:raise
        except Exception:
            self.failed=True;self.final.set()
            await self.push_frame(ErrorFrame('火山语音识别连接或协议失败，请检查凭证、资源授权与网络后手动重试'))

    async def _start(self):
        import uuid
        ip=await public_ip()
        headers={'X-Api-Key':settings.volc_asr_api_key,'X-Api-Resource-Id':settings.volc_asr_resource_id,
                 'X-Api-Connect-Id':str(uuid.uuid4())}
        self.socket=await self.factory(URL,additional_headers=headers,host=ip,port=443,
            ssl=ssl.create_default_context(),server_hostname=HOST,proxy=None,
            open_timeout=10,close_timeout=2,max_size=MAX_RESULT,max_queue=8)
        initial={'audio':{'format':'pcm','codec':'raw','rate':16000,'bits':16,'channel':1},
                 'request':{'model_name':'bigmodel','enable_itn':True,'enable_punc':True,'show_utterances':True,'result_type':'full'}}
        await self.socket.send(request_packet(json.dumps(initial).encode()))
        self.reader=asyncio.create_task(self._read())

    async def _finish(self):
        if self.stopped:return
        self.stopped=True
        await self.socket.send(request_packet(bytes(self.buffer),audio=True,last=True));self.buffer.clear()
        try:await asyncio.wait_for(self.final.wait(),5)
        except TimeoutError:
            self.failed=True
            await self.push_frame(ErrorFrame('语音收尾超时，未确认最终文本；请检查输入框后手动重试'))
        if not self.failed:await self.push_frame(VoiceDoneFrame())

    async def process_frame(self,frame,direction):
        await super().process_frame(frame,direction)
        if isinstance(frame,StartFrame):
            try:await self._start()
            except Exception:
                self.failed=True
                await self.push_frame(frame,direction)
                await self.push_frame(ErrorFrame('火山语音连接失败，请检查API Key、资源授权与网络'))
                return
        elif isinstance(frame,InputAudioRawFrame):
            if self.failed or self.stopped:return
            if frame.sample_rate!=16000 or frame.num_channels!=1:raise ASRProtocolError('invalid audio')
            self.buffer.extend(frame.audio)
            # 200ms PCM16/16k mono: official recommended packet size.
            while len(self.buffer)>=6400:
                await self.socket.send(request_packet(bytes(self.buffer[:6400]),audio=True));del self.buffer[:6400]
            return
        elif isinstance(frame,VADUserStoppedSpeakingFrame):
            if self.socket and not self.failed:await self._finish()
            return
        elif isinstance(frame,(CancelFrame,EndFrame)):
            await self._close()
        await self.push_frame(frame,direction)

    async def _close(self):
        self.buffer.clear()
        if self.reader and self.reader is not asyncio.current_task():
            self.reader.cancel()
            with contextlib.suppress(asyncio.CancelledError):await self.reader
            self.reader=None
        if self.socket:
            with contextlib.suppress(Exception):await self.socket.close()
            self.socket=None

    async def cleanup(self):
        await self._close()
        await super().cleanup()
