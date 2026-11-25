import {afterEach,describe,expect,it,vi} from 'vitest';
import {createElement,act} from 'react';
import {createRoot} from 'react-dom/client';
import type {Root} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import {EditorPage} from './Editor';
import type {Message, Build} from '../lib/types';
const state=vi.hoisted(()=>({run:{id:'r',status:'queued',requires_resubmit:true,mock:false,events:[],error:null,stream_bytes:0},messages:[] as Message[],build:null as Build|null,ready:false,calls:[] as string[]}));
vi.mock('../AppContext',()=>({useApp:()=>({user:{id:'u'},model:{id:'m',provider:'deepseek',version:1},refreshModel:vi.fn(),meta:{features:{}},setModelOpen:vi.fn()})}));
vi.mock('../components/VoiceInput',()=>({VoiceInput:()=>createElement('button',{'aria-label':'开始语音输入'},createElement('svg'))}));
vi.mock('../lib/api',()=>({ApiError:class extends Error{},errorText:(e:Error)=>e.message,api:async(path:string,options?:RequestInit)=>{
 state.calls.push(`${options?.method??'GET'} ${path}`);
 if(path.endsWith('/snapshot'))return {run:state.run,build:state.build,messages:state.messages};
 if(path.endsWith('/publication'))return {status:'unpublished'};
 if(path.includes('service-status'))return {worker_ready:state.ready,preview_ready:state.ready,publication_ready:state.ready,can_generate:state.ready};
 if(path.includes('/stream?'))return {run_id:'r',revision:0,offset:0,next_offset:0,delta:'',reset:false,stream_bytes:0,status:'queued'};
 return {id:'p',name:'测试项目'};
}}));
let root:Root|undefined;
afterEach(async()=>{if(root)await act(async()=>root!.unmount());root=undefined;document.body.replaceChildren();state.calls=[];state.messages=[];state.build=null;state.ready=false;state.run.status='queued';state.run.requires_resubmit=true;vi.unstubAllGlobals();});
describe('editor component interactions, not browser E2E',()=>{
 it('shows blocked state without fake code and service check is read only',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);const container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(EditorPage))));
  expect(container.textContent).toContain('旧需求待确认');expect(container.textContent).toContain('旧需求等待重新确认');
  const check=Array.from(container.querySelectorAll('button')).find(x=>x.textContent==='检查服务')!;
  await act(async()=>check.click());expect(state.calls.every(x=>x.startsWith('GET '))).toBe(true);
  const send=container.querySelector<HTMLButtonElement>('[aria-label="发送修改需求"]')!;expect(send.disabled).toBe(true);expect(send.previousElementSibling?.getAttribute('aria-label')).toBe('开始语音输入');
  const codeTab=Array.from(container.querySelectorAll<HTMLButtonElement>('[role=tab]')).find(x=>x.textContent==='代码')!;
  await act(async()=>codeTab.click());expect(codeTab.getAttribute('aria-selected')).toBe('true');
  expect(container.querySelector('.code-view')).toBeNull();
 });
 it('separates user and Agent rows and places stop at composer send slot',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);state.run.status='generating';state.run.requires_resubmit=false;state.ready=true;
  state.messages=[{id:'u1',role:'user',content:'做一个清单',created_at:'2026-11-25T00:00:00Z'},{id:'a1',role:'assistant',content:'正在整理需求',created_at:'2026-11-25T00:00:01Z'}];
  const container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(EditorPage))));
  expect(container.querySelector('.message-row.from-user .message.user')?.textContent).toContain('做一个清单');
  expect(container.querySelector('.message-row.from-agent .message.assistant')?.textContent).toContain('正在整理需求');
  const stop=container.querySelector<HTMLButtonElement>('[aria-label="停止生成"]')!;
  expect(stop.closest('.chat-composer .prompt-footer')).not.toBeNull();expect(stop.previousElementSibling?.getAttribute('aria-label')).toBe('开始语音输入');
  expect(container.querySelector('[aria-label="发送修改需求"]')).toBeNull();expect(stop.textContent).toBe('');
  await act(async()=>stop.click());expect(container.textContent).toContain('停止生成？');expect(state.calls.some(x=>x.endsWith('/stop'))).toBe(false);
  const confirm=Array.from(container.querySelectorAll<HTMLButtonElement>('button')).find(x=>x.textContent==='确认停止')!;
  await act(async()=>confirm.click());expect(state.calls.filter(x=>x.startsWith('POST ')&&x.endsWith('/stop')).length).toBe(1);
 });
 it('shows disabled stop spinner while cancellation is pending',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);state.run.status='cancelling';state.run.requires_resubmit=false;state.ready=true;
  const container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(EditorPage))));
  const stop=container.querySelector<HTMLButtonElement>('[aria-label="停止中"]')!;expect(stop.disabled).toBe(true);expect(stop.querySelector('.spinner')).not.toBeNull();expect(container.querySelector('[aria-label="发送修改需求"]')).toBeNull();
 });
 it('renders two build-bound suggestions and clicking only fills the draft',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);state.run.status='succeeded';state.run.requires_resubmit=false;state.ready=true;
  state.build={id:'b',number:1,validation:{},mock:false,suggestions:[{label:'增加归档',prompt:'增加笔记归档，保留现有数据。'},{label:'优化标签展示',prompt:'优化标签展示，保留搜索与数据。'}]};
  const container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(EditorPage))));
  expect(container.querySelectorAll('.suggestions button').length).toBe(2);expect(container.querySelector('.suggestions')?.getAttribute('aria-label')).toBe('下一步建议');
  const button=container.querySelector<HTMLButtonElement>('.suggestions button')!;await act(async()=>button.click());
  expect(container.querySelector<HTMLTextAreaElement>('[aria-label="修改需求"]')!.value).toBe('增加笔记归档，保留现有数据。');
  expect(state.calls.every(x=>x.startsWith('GET '))).toBe(true);expect(container.querySelector('.suggestions')?.textContent).not.toContain('改成深色主题');
 });
 it('does not invent fixed suggestions for legacy builds without metadata',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);state.run.status='succeeded';state.run.requires_resubmit=false;
  state.build={id:'b',number:1,validation:{},mock:false};
  const container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(EditorPage))));
  expect(container.querySelector('.suggestions')).toBeNull();expect(state.calls.every(x=>x.startsWith('GET '))).toBe(true);
 });
});
