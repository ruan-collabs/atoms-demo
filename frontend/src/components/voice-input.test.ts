import {afterEach,describe,expect,it,vi} from 'vitest';
import {createElement,act} from 'react';
import {createRoot} from 'react-dom/client';
import type {Root} from 'react-dom/client';
import {VoiceInput} from './VoiceInput';
vi.mock('../AppContext',()=>({useApp:()=>({user:{id:'fixture',email:'fixture@example.com'}})}));
vi.mock('../lib/api',()=>({api:()=>Promise.resolve({enabled:true,provider:'pipecat-volcengine',provider_name:'火山引擎',max_seconds:60,message:'configured'}),errorText:(e:Error)=>e.message}));
let root:Root|undefined;
afterEach(async()=>{if(root)await act(async()=>root!.unmount());root=undefined;document.body.replaceChildren();vi.unstubAllGlobals();});
describe('voice icon interaction',()=>{
 it('is icon-only and click requests microphone without business confirm',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);vi.stubGlobal('isSecureContext',true);vi.stubGlobal('AudioWorkletNode',class {});
  const request=vi.fn().mockRejectedValue(new Error('mic test rejected'));Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:request}});
  const confirm=vi.spyOn(window,'confirm').mockImplementation(()=>{throw Error('unexpected confirmation');});
  const status=vi.fn(),container=document.createElement('div');document.body.append(container);root=createRoot(container);
  await act(async()=>{root!.render(createElement(VoiceInput,{value:'',onChange:vi.fn(),onStatusChange:status}));});
  const button=container.querySelector('button')!;expect(button.textContent).toBe('');expect(button.querySelector('svg')).not.toBeNull();expect(button.disabled).toBe(false);
  expect(status).toHaveBeenLastCalledWith('');expect(button.title).toBe('开始语音输入');
  await act(async()=>{button.click();});
  expect(request).toHaveBeenCalledOnce();expect(confirm).not.toHaveBeenCalled();expect(status).toHaveBeenCalledWith('mic test rejected');confirm.mockRestore();
 });
});
