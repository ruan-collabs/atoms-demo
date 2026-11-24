import uuid
import pytest
from app.api import model_config

@pytest.mark.parametrize('provider,url',[('openai','https://api.openai.com/v1'),('custom','https://api.deepseek.com')])
def test_unreleased_provider_cannot_send_test_request(client,login,monkeypatch,provider,url):
 login(client)
 async def unexpected(*args,**kwargs):raise AssertionError('unreleased provider must not call upstream')
 monkeypatch.setattr(model_config,'completion',unexpected)
 response=client.post('/api/model-config/test',json={'provider':provider,'api_key':'fixture-only-key','base_url':url,'model':'fixture','idempotency_key':str(uuid.uuid4()),'consent':True})
 assert response.status_code==422 and '模型未上线' in response.json()['detail']
