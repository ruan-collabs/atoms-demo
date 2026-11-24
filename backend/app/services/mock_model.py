import asyncio
import json
from pathlib import Path
from app.config import settings
from app.services.provider import ProviderError

async def mock_completion(prompt,base_html=None,planning=False):
    if settings.production or not settings.dev_mock_model:raise ProviderError('Mock模型不可用','mock')
    await asyncio.sleep(20 if '[mock:slow]' in prompt else settings.mock_delay_seconds)
    if '[mock:fail]' in prompt:raise ProviderError('开发Mock注入：供应商失败','upstream')
    if planning:return json.dumps({'scope':'开发Mock验证','components':['输入','列表','状态筛选'],'storage':'当前项目独立Origin localStorage','acceptance':['添加','修改','持久化'],'mock':True},ensure_ascii=False)
    if '[mock:invalid]' in prompt:return '<html>invalid'
    if base_html:
        html=base_html
        if '紫' in prompt:html=html.replace('--accent:#4f74ed','--accent:#8b5cf6')
        if '绿' in prompt:html=html.replace('--accent:#4f74ed','--accent:#22a06b').replace('--accent:#8b5cf6','--accent:#22a06b')
        return html
    name='portfolio.html' if ('作品' in prompt or 'portfolio' in prompt.lower()) else 'tasks.html'
    return (Path(__file__).resolve().parents[1]/'fixtures'/name).read_text(encoding='utf-8')
