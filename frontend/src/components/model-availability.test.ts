import {afterEach,describe,expect,it,vi} from 'vitest';
import {act,createElement} from 'react';
import {createRoot} from 'react-dom/client';
import type {Root} from 'react-dom/client';
import {ModelModal} from './ModelModal';
const state=vi.hoisted(()=>({user:{email:'fixture@example.com'},model:null as null|{provider:string;base_url:string;model:string},meta:{features:{mock_model:true}},setModelOpen:vi.fn(),refreshModel:vi.fn()}));
const request=vi.hoisted(()=>vi.fn());
vi.mock('../AppContext',()=>({useApp:()=>state}));
vi.mock('../lib/api',()=>({api:request,errorText:(e:Error)=>e.message}));
let root:Root|undefined;
afterEach(async()=>{if(root)await act(async()=>root!.unmount());root=undefined;document.body.replaceChildren();state.user.email='fixture@example.com';state.model=null;vi.clearAllMocks();vi.unstubAllGlobals();});
async function mount(){vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);const container=document.createElement('div');document.body.append(container);root=createRoot(container);await act(async()=>root!.render(createElement(ModelModal)));return container;}

describe('model availability UI',()=>{
 it('defaults to DeepSeek for real account even when Mock feature is enabled',async()=>{const c=await mount();const selected=c.querySelector('.provider-tabs button.selected')!;expect(selected.textContent).toBe('DeepSeek');expect(selected.getAttribute('aria-pressed')).toBe('true');expect(c.querySelector('.provider-tabs')?.textContent).not.toContain('开发Mock');});
 it('disables unreleased providers with hover/focus tooltip and no request on click',async()=>{const c=await mount();const options=c.querySelectorAll('.provider-option.unavailable');expect(options.length).toBe(2);for(const option of options){const button=option.querySelector('button')!;expect(button.disabled).toBe(true);expect(option.getAttribute('tabindex')).toBe('0');expect(option.querySelector('[role=tooltip]')?.textContent).toBe('模型未上线');await act(async()=>button.click());}expect(c.querySelector('.selected')?.textContent).toBe('DeepSeek');expect(request).not.toHaveBeenCalled();});
 it('keeps Mock only for explicit development identity',async()=>{state.user.email='alice@mock.invalid';const c=await mount();expect(c.querySelector('.selected')?.textContent).toBe('开发Mock');});
 it('does not reuse an old unavailable provider endpoint as DeepSeek',async()=>{state.model={provider:'openai',base_url:'https://api.openai.com/v1',model:'old-model'};const c=await mount();expect(c.querySelector('.selected')?.textContent).toBe('DeepSeek');const values=Array.from(c.querySelectorAll<HTMLInputElement>('input')).map(x=>x.value);expect(values).toContain('https://api.deepseek.com');expect(values).not.toContain('https://api.openai.com/v1');});
});
