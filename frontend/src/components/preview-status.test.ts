import {afterEach,describe,expect,it,vi} from 'vitest';
import {createElement,act} from 'react';
import {createRoot} from 'react-dom/client';
import type {Root} from 'react-dom/client';
import {ApplicationPreview} from './ApplicationPreview';
import {MockPreview} from './MockPreview';
let root:Root|undefined;
afterEach(async()=>{if(root)await act(async()=>root!.unmount());root=undefined;document.body.replaceChildren();vi.restoreAllMocks();vi.unstubAllGlobals();});

async function mount(mock=false){
 vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);
 const container=document.createElement('div');document.body.append(container);root=createRoot(container);
 await act(async()=>root!.render(mock?createElement(MockPreview,{html:'fixture-only',projectId:'p',ownerId:'u'}):createElement(ApplicationPreview,{projectId:'p',buildId:'b',ownerId:'u'})));
 const frame=container.querySelector('iframe')!;
 const channel=new URL(frame.src).searchParams.get('channel');
 const message=async(type:string,overrides:Record<string,unknown>={})=>{
  await act(async()=>{window.dispatchEvent(new MessageEvent('message',{source:frame.contentWindow,origin:'null',data:{type,channel,...(mock?{}:{buildId:'b'}),...overrides}}));});
 };
 return {container,frame,message};
}

describe('preview success notice removal (component contracts, not browser E2E)',()=>{
 it.each([false,true])('removes successful status row without changing sandbox (mock=%s)',async(mock)=>{
  const {container,frame,message}=await mount(mock);
  expect(container.querySelector('[role=status]')).not.toBeNull();
  await message('init-request');await message('ready');
  expect(container.querySelector('[role=status]')).toBeNull();
  expect(frame.getAttribute('sandbox')).toBe('allow-scripts allow-forms');
  expect(frame.getAttribute('referrerpolicy')).toBe('no-referrer');
  await message('error');
  expect(container.querySelector('[role=status]')?.textContent).toContain('运行错误');
 });
 it('ignores ready from wrong channel and keeps loading feedback',async()=>{
  const {container,message}=await mount();await message('init-request');await message('ready',{channel:'wrong'});
  expect(container.querySelector('[role=status]')?.textContent).toBe('沙箱加载中…');
 });
 it.each([false,true])('does not hide storage initialization failure on ready (mock=%s)',async(mock)=>{
  const {container,message}=await mount(mock);
  vi.spyOn(Storage.prototype,'getItem').mockImplementation(()=>{throw Error('fixture storage failure');});
  await message('init-request');await message('ready');
  expect(container.querySelector('[role=status]')?.textContent).toContain('存储不可用');
 });
});
