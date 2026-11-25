import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {act, createElement} from 'react';
import {createRoot, type Root} from 'react-dom/client';
import {MemoryRouter} from 'react-router-dom';
import {ProjectsPage} from './Projects';

const state=vi.hoisted(()=>({calls:[] as string[]}));
vi.mock('../AppContext',()=>({useApp:()=>({user:{id:'fixture',email:'fixture@example.com'}})}));
vi.mock('./Dashboard',()=>({ProjectCard:()=>null}));
vi.mock('../lib/api',()=>({errorText:(e:Error)=>e.message,api:async(path:string)=>{state.calls.push(path);return {items:[],total:0,has_more:false};}}));
let root:Root;
let container:HTMLDivElement;
beforeEach(()=>{vi.useFakeTimers();vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);state.calls=[];container=document.createElement('div');document.body.append(container);root=createRoot(container);});
afterEach(async()=>{await act(async()=>root.unmount());document.body.replaceChildren();vi.useRealTimers();vi.unstubAllGlobals();});
const mount=async()=>{await act(async()=>root.render(createElement(MemoryRouter,null,createElement(ProjectsPage))));await act(async()=>vi.advanceTimersByTimeAsync(260));};

describe('project status filter component, not live API E2E',()=>{
  it('keeps native keyboard-accessible select in styled wrapper with decorative chevron',async()=>{
    await mount();
    const select=container.querySelector<HTMLSelectElement>('[aria-label="筛选项目状态"]')!;
    expect(select.closest('.project-status-filter')).not.toBeNull();
    expect(select.value).toBe('all');
    expect(Array.from(select.options).map(option=>[option.value,option.text])).toEqual([['all','全部'],['preview','可预览'],['active','生成中'],['failed','失败']]);
    expect(select.nextElementSibling?.getAttribute('aria-hidden')).toBe('true');
    expect(select.disabled).toBe(false);
  });
  it('switches every existing filter and preserves search in read-only list requests',async()=>{
    await mount();
    const select=container.querySelector<HTMLSelectElement>('[aria-label="筛选项目状态"]')!;
    for(const value of ['preview','active','failed','all']){
      await act(async()=>{select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));});
      await act(async()=>vi.advanceTimersByTimeAsync(260));
      expect(state.calls.at(-1)).toBe(`/projects?status=${value}&q=`);
    }
    const input=container.querySelector<HTMLInputElement>('[aria-label="搜索项目名称"]')!;
    await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,'任务');input.dispatchEvent(new Event('input',{bubbles:true}));});
    await act(async()=>vi.advanceTimersByTimeAsync(260));
    expect(state.calls.at(-1)).toBe(`/projects?status=all&q=${encodeURIComponent('任务')}`);
    expect(state.calls).toHaveLength(6);
  });
});
