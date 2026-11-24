"""Pipecat STT-only adapter. Raw PCM16 -> interim/final text; no LLM/TTS or recording."""
import asyncio
import json
from pipecat.frames.frames import EndFrame, InputAudioRawFrame, TranscriptionFrame, InterimTranscriptionFrame, Frame, ErrorFrame, VADUserStoppedSpeakingFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.workers.runner import WorkerRunner
from pipecat.pipeline.worker import PipelineWorker, PipelineParams
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.serializers.base_serializer import FrameSerializer
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from loguru import logger
from app.config import settings
from app.services.volcengine_asr import VolcengineSTTProcessor, VoiceDoneFrame

# Third-party connection errors can contain credential material. No raw SDK logs.
logger.disable('pipecat')
logger.disable('deepgram')

class PCMSerializer(FrameSerializer):
    def __init__(self):
        super().__init__()
        self.received_bytes=0
    async def serialize(self, frame: Frame):
        return None
    async def deserialize(self, data):
        if isinstance(data,bytes):
            if not data or len(data)%2 or len(data)>8192:raise ValueError('invalid PCM packet')
            self.received_bytes+=len(data)
            if self.received_bytes>16000*2*min(settings.voice_max_seconds,120):raise ValueError('audio limit')
            return InputAudioRawFrame(data,16000,1)
        if len(data)>256:raise ValueError('control limit')
        message=json.loads(data)
        if message=={'type':'stop'}:return VADUserStoppedSpeakingFrame()
        raise ValueError('invalid control')

class TranscriptOutput(FrameProcessor):
    def __init__(self, websocket):
        super().__init__()
        self.websocket=websocket
        self.seq=0
    async def process_frame(self,frame,direction):
        await super().process_frame(frame,direction)
        if isinstance(frame,(TranscriptionFrame,InterimTranscriptionFrame)):
            self.seq+=1
            await self.websocket.send_json({'type':'transcript','seq':self.seq,'text':frame.text[:4000],
                                            'final':not isinstance(frame,InterimTranscriptionFrame),
                                            'replace':bool(isinstance(frame.result,dict) and frame.result.get('replace'))})
        elif isinstance(frame,VoiceDoneFrame):
            await self.websocket.send_json({'type':'done'})
        elif isinstance(frame,ErrorFrame):
            await self.websocket.send_json({'type':'error','message':'语音识别服务不可用，请检查服务端配置后重试'})
        await self.push_frame(frame,direction)

async def run_transcription(websocket):
    transport=FastAPIWebsocketTransport(websocket,FastAPIWebsocketParams(
        audio_in_enabled=True,audio_out_enabled=False,serializer=PCMSerializer(),
        allowed_origins=[settings.public_origin],session_timeout=min(settings.voice_max_seconds,120)))
    if settings.voice_provider=='volcengine':
        stt=VolcengineSTTProcessor()
    else:
        stt=DeepgramSTTService(api_key=settings.deepgram_api_key,sample_rate=16000,encoding='linear16',channels=1,
            mip_opt_out=True,settings=DeepgramSTTService.Settings(model=settings.voice_model,
            language=settings.voice_language,interim_results=True,punctuate=True,endpointing=300))
    worker=PipelineWorker(Pipeline([transport.input(),stt,TranscriptOutput(websocket),transport.output()]),
        enable_rtvi=False,enable_turn_tracking=False,params=PipelineParams(audio_in_sample_rate=16000),
        idle_timeout_secs=20,cancel_timeout_secs=3)
    @transport.event_handler('on_client_disconnected')
    async def disconnected(transport,websocket):
        await worker.cancel()
    @transport.event_handler('on_session_timeout')
    async def timed_out(transport,websocket):
        await worker.cancel()
    @transport.event_handler('on_client_connected')
    async def connected(transport,websocket):
        await websocket.send_json({'type':'ready','sample_rate':16000,'channels':1,'format':'pcm16',
                                   'max_seconds':min(settings.voice_max_seconds,120)})
    runner=WorkerRunner(handle_sigint=False)
    try:
        async with asyncio.timeout(min(settings.voice_max_seconds,120)+5):
            await runner.add_workers(worker)
            await runner.run()
    finally:
        try:
            await worker.cancel()
        finally:
            if settings.voice_provider=='volcengine':
                await stt._close()
