import { describe, expect, it, vi } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { ProtectedLayout } from '../components/Layout';
import { ModelModal } from '../components/ModelModal';
import { LoginPage } from '../pages/Login';
import { DashboardPage } from '../pages/Dashboard';

const state=vi.hoisted(()=>({user:null as {id:string;email:string}|null,model:null,modelOpen:false,meta:{mail_mode:'file',features:{google_login:false},model_allowed_origins:['https://api.openai.com']},setModelOpen:vi.fn(),saveModel:vi.fn(),clearModel:vi.fn(),logout:vi.fn()}));
vi.mock('../AppContext',()=>({useApp:()=>state,rememberedModel:()=>null}));
const render=(component:React.ComponentType)=>renderToStaticMarkup(createElement(MemoryRouter,null,createElement(component)));

describe('page-shell contract (component tests, not browser E2E)',()=>{
  it('shows Google login disabled when OAuth configuration is missing',()=>{state.user=null;state.meta.features.google_login=false;const html=render(LoginPage);expect(html).toContain('使用 Google 登录');expect(html).toContain('待配置');expect(html).not.toContain('不支持第三方登录');});
  it('only shows Google business login and visitor browse, not email or Mock entry',()=>{state.user=null;const html=render(LoginPage);expect(html).toContain('目前仅支持 Google 登录');expect(html).toContain('先浏览工作台');expect(html).not.toContain('发送邮箱验证码');expect(html).not.toContain('type="email"');expect(html).not.toContain('href="/dev-test"');});
  it('authenticated unconfigured user receives gate not project content',()=>{state.user={id:'fixture',email:'fixture@example.com'};state.modelOpen=false;const html=render(ProtectedLayout);expect(html).toContain('先连接你的模型');expect(html).not.toContain('最近的项目');});
  it('closed modal does not remove gate and logout remains available',()=>{state.modelOpen=false;const html=render(ProtectedLayout);expect(html).toContain('配置模型');expect(html).toContain('退出登录');});
  it('guest can see dashboard and query field without login redirect',()=>{state.user=null;const html=render(DashboardPage);expect(html).toContain('你想创造什么');expect(html).toContain('应用需求');expect(html).toContain('发送后登录');});
  it('places one icon-only microphone immediately before dashboard send',()=>{state.user=null;const html=render(DashboardPage);const doc=new DOMParser().parseFromString(html,'text/html');const send=doc.querySelector('button[aria-label="开始生成项目"]')!;const mic=send.previousElementSibling!;expect(mic.getAttribute('aria-label')).toBe('开始语音输入');expect(mic.textContent).toBe('');expect(doc.querySelectorAll('.voice-button').length).toBe(1);});
  it('model dialog initially blocks save until actual test succeeds',()=>{state.modelOpen=true;const html=render(ModelModal);expect(html).toContain('保存并启用');expect(html).toContain('测试连接');expect(html).toContain('服务器受控出站');expect(html.match(/disabled=""/g)?.length).toBeGreaterThanOrEqual(2);});
});
