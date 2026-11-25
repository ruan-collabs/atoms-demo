import {afterEach,describe,expect,it,vi} from 'vitest';
import {act,createElement} from 'react';
import {createRoot} from 'react-dom/client';
import type {Root} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import {LoginPage} from './Login';
const state=vi.hoisted(()=>({user:null,meta:{features:{google_login:true,mock_auth:true}}}));
const request=vi.hoisted(()=>vi.fn());
vi.mock('../AppContext',()=>({useApp:()=>state}));
vi.mock('../lib/api',()=>({api:request,errorText:(e:Error)=>e.message}));
let root:Root|undefined;
afterEach(async()=>{if(root)await act(async()=>root!.unmount());root=undefined;document.body.replaceChildren();vi.clearAllMocks();vi.unstubAllGlobals();});
describe('Google click consent without checkbox',()=>{
 it('starts only on click, prevents duplicate starts and recovers from failure',async()=>{
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);
  let reject:(e:Error)=>void=()=>{};request.mockImplementation(()=>new Promise((_,r)=>{reject=r;}));
  const c=document.createElement('div');document.body.append(c);root=createRoot(c);
  await act(async()=>root!.render(createElement(MemoryRouter,null,createElement(LoginPage))));
  const button=c.querySelector<HTMLButtonElement>('.google-button')!;
  expect(button.disabled).toBe(false);expect(request).not.toHaveBeenCalled();expect(c.querySelector('input[type=checkbox]')).toBeNull();
  await act(async()=>{button.click();button.click();});
  expect(request).toHaveBeenCalledOnce();expect(request.mock.calls[0][0]).toBe('/auth/google/start');
  expect(JSON.parse(request.mock.calls[0][1].body)).toEqual({terms_accepted:true});expect(button.disabled).toBe(true);
  await act(async()=>{reject(new Error('fixture connection error'));});
  expect(button.disabled).toBe(false);expect(c.textContent).toContain('fixture connection error');expect(c.querySelector('a[href="/dev-test"]')).not.toBeNull();
 });
});
