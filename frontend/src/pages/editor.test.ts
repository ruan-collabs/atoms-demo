import {afterEach,describe,expect,it,vi} from 'vitest';
import {createElement,act} from 'react';
import {createRoot} from 'react-dom/client';
import type {Root} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import {EditorPage} from './Editor';
const state=vi.hoisted(()=>({run:{id:'r',status:'queued',requires_resubmit:true,mock:false,events:[],error:null,stream_bytes:0},calls:[] as string[]}));
vi.mock('../AppContext',()=>({useApp:()=>({user:{id:'u'},model:{id:'m',provider:'deepseek',version:1},refreshModel:vi.fn(),meta:{features:{}},setModelOpen:vi.fn()})}));
vi.mock('../components/VoiceInput',()=>({VoiceInput:()=>createElement('button',{'aria-label':'开始语音输入'},createElement('svg'))}));
vi.mock('../lib/api',()=>({ApiError:class extends Error{},errorText:(e:Error)=>e.message,api:async(path:string,options?:RequestInit)=>{
 state.calls.push(`${options?.method??'GET'} ${path}`);
 if(path.endsWith('/snapshot'))return {run:state.run,build:null,messages:[]};
 if(path.endsWith('/publication'))return {status:'unpublished'};
 if(path.includes('service-status'))return {worker_ready:false,preview_ready:false,publication_ready:false,can_generate:false};
 if(path.includes('/stream?'))return {run_id:'r',revision:0,offset:0,next_offset:0,delta:'',reset:false,stream_bytes:0,status:'queued'};
 return {id:'p',name:'测试项目'};
}}));
let root:Root|undefined;
afterEach(async()=>{if(root)await act(async()=>root!.unmount());root=undefined;document.body.replaceChildren();state.calls=[];vi.unstubAllGlobals();});
describe('editor component interactions, not browser E2E',()=>{
 it('shows blocked state without fake code and service check is read only',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);const container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(EditorPage))));
  expect(container.textContent).toContain('尚未开始生成');expect(container.textContent).toContain('生成服务未就绪');
  const check=Array.from(container.querySelectorAll('button')).find(x=>x.textContent==='检查服务')!;
  await act(async()=>check.click());expect(state.calls.every(x=>x.startsWith('GET '))).toBe(true);
  const send=container.querySelector<HTMLButtonElement>('[aria-label="发送修改需求"]')!;expect(send.disabled).toBe(true);expect(send.previousElementSibling?.getAttribute('aria-label')).toBe('开始语音输入');
  const codeTab=Array.from(container.querySelectorAll<HTMLButtonElement>('[role=tab]')).find(x=>x.textContent==='代码')!;
  await act(async()=>codeTab.click());expect(codeTab.getAttribute('aria-selected')).toBe('true');
  expect(container.querySelector('.code-view')).toBeNull();
 });
});
