import asyncio
import pytest
from starlette.websockets import WebSocketDisconnect
from app.config import settings

@pytest.fixture(autouse=True)
def default_voice_provider(monkeypatch):
    monkeypatch.setattr(settings,'voice_provider','deepgram')

def test_voice_status_unconfigured_is_clear(client,monkeypatch):
    monkeypatch.setattr(settings,'voice_enabled',False)
    result=client.get('/api/voice/status')
    assert result.status_code==200 and result.json()['enabled'] is False
    assert 'DEEPGRAM_API_KEY' in result.json()['message']

def test_voice_websocket_requires_origin_and_login(client,monkeypatch):
    monkeypatch.setattr(settings,'voice_enabled',True)
    monkeypatch.setattr(settings,'deepgram_api_key','fixture-not-real')
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/api/voice/ws',headers={'Origin':'https://invalid.example'}):pass
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/api/voice/ws',headers={'Origin':settings.public_origin}):pass

def test_pipecat_pipeline_websocket_audio_transcript_and_close(client,monkeypatch):
    from app.services import voice
    from pipecat.processors.frame_processor import FrameProcessor
    from pipecat.frames.frames import InputAudioRawFrame,InterimTranscriptionFrame,TranscriptionFrame
    from app.api.voice import active_sessions
    class FakeSTT(FrameProcessor):
        def __init__(self,**kwargs):super().__init__()
        async def process_frame(self,frame,direction):
            await super().process_frame(frame,direction)
            if isinstance(frame,InputAudioRawFrame):
                await self.push_frame(InterimTranscriptionFrame('创建任务','fixture',''),direction)
                await self.push_frame(TranscriptionFrame('创建任务板','fixture',''),direction)
            else:await self.push_frame(frame,direction)
    FakeSTT.Settings=voice.DeepgramSTTService.Settings
    monkeypatch.setattr(voice,'DeepgramSTTService',FakeSTT)
    # The fake service replaces only STT; Pipecat transport/serializer/worker are real.
    monkeypatch.setattr(settings,'voice_enabled',True)
    monkeypatch.setattr(settings,'deepgram_api_key','fixture-not-real')
    monkeypatch.setattr(settings,'dev_mock_auth',True)
    assert client.post('/api/dev/mock-login',json={'account':'alice'}).status_code==200
    with client.websocket_connect('/api/voice/ws',headers={'Origin':settings.public_origin}) as ws:
        assert ws.receive_json()['type']=='ready'
        ws.send_bytes(bytes(640))
        first=ws.receive_json();second=ws.receive_json()
        assert first['text']=='创建任务' and first['final'] is False
        assert second['text']=='创建任务板' and second['final'] is True
        assert first['seq']<second['seq']
    assert not active_sessions


def test_pcm_serializer_bounds_and_stop():
    from app.services.voice import PCMSerializer
    from pipecat.frames.frames import InputAudioRawFrame,VADUserStoppedSpeakingFrame
    serializer=PCMSerializer()
    frame=asyncio.run(serializer.deserialize(bytes(640)))
    assert isinstance(frame,InputAudioRawFrame) and frame.sample_rate==16000 and frame.num_channels==1
    assert isinstance(asyncio.run(serializer.deserialize('{"type":"stop"}')),VADUserStoppedSpeakingFrame)
    for value in [b'x',bytes(8194),'{"type":"generate"}']:
        with pytest.raises(ValueError):asyncio.run(serializer.deserialize(value))
