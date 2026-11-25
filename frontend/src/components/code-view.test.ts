import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { CodeView } from './CodeView';

let root: Root;
let container: HTMLDivElement;
let height = 100;
let contentHeight = 500;
let props = {code:'first',runId:'r1',generating:true,visible:true,panel:'workspace'};
const mount = async () => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  vi.spyOn(HTMLElement.prototype, 'clientHeight', 'get').mockImplementation(() => height);
  vi.spyOn(HTMLElement.prototype, 'scrollHeight', 'get').mockImplementation(() => contentHeight);
  container = document.createElement('div');document.body.append(container);root = createRoot(container);
  await act(async () => root.render(createElement(CodeView, props)));
  return container.querySelector('pre')!;
};
const update = async () => { await act(async () => root.render(createElement(CodeView, props))); };
afterEach(async () => {
  if (root) await act(async () => root.unmount());
  document.body.replaceChildren();vi.restoreAllMocks();vi.unstubAllGlobals();
  height = 100;contentHeight = 500;
  props = {code:'first',runId:'r1',generating:true,visible:true,panel:'workspace'};
});

describe('code stream follow (component tests, not browser geometry)', () => {
  it('follows appended code and ignores its own scroll events without changing horizontal scroll', async () => {
    const pre = await mount();expect(pre.scrollTop).toBe(400);
    pre.scrollLeft = 48;pre.dispatchEvent(new Event('scroll'));
    contentHeight = 700;props.code += '\nnext';await update();
    expect(pre.scrollTop).toBe(600);expect(pre.scrollLeft).toBe(48);
  });
  it('manual wheel pauses for this run even across tab changes and stream resets', async () => {
    const pre = await mount();pre.dispatchEvent(new WheelEvent('wheel',{bubbles:true,deltaY:-60}));pre.scrollTop = 180;
    contentHeight = 700;props.code += '\nnext';await update();expect(pre.scrollTop).toBe(180);
    props.visible = false;await update();props.visible = true;props.code = 'retry revision';await update();expect(pre.scrollTop).toBe(180);
    props.runId = 'r2';await update();expect(pre.scrollTop).toBe(600);
  });
  it('keyboard and touch manual reading pause follow', async () => {
    const pre = await mount();pre.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'PageUp'}));pre.scrollTop = 90;
    contentHeight = 650;props.code += 'more';await update();expect(pre.scrollTop).toBe(90);
    props.runId = 'r2';await update();pre.dispatchEvent(new Event('touchmove',{bubbles:true}));pre.scrollTop = 50;
    contentHeight = 800;props.code += 'more';await update();expect(pre.scrollTop).toBe(50);
  });
  it('native scrollbar movement pauses but clicking/selecting code does not', async () => {
    const pre = await mount();pre.dispatchEvent(new MouseEvent('pointerdown',{bubbles:true}));
    contentHeight = 600;props.code += 'more';await update();expect(pre.scrollTop).toBe(500);
    pre.scrollTop = 120;pre.dispatchEvent(new Event('scroll'));contentHeight = 800;props.code += 'more';await update();expect(pre.scrollTop).toBe(120);
  });
  it('does not scroll hidden tabs or finished builds, follows when generating code becomes visible', async () => {
    props.visible = false;const pre = await mount();expect(pre.scrollTop).toBe(0);
    contentHeight = 700;props.code += 'more';await update();expect(pre.scrollTop).toBe(0);
    props.visible = true;await update();expect(pre.scrollTop).toBe(600);
    props.generating = false;contentHeight = 900;props.code += 'final';await update();expect(pre.scrollTop).toBe(600);
  });
  it('skips zero-height mobile-hidden panel and follows once workspace is shown', async () => {
    height = 0;const pre = await mount();expect(pre.scrollTop).toBe(0);
    height = 100;props.panel = 'chat';await update();expect(pre.scrollTop).toBe(400);
  });
  it('retains manual pause when retry revision temporarily clears code', async () => {
    const pre = await mount();pre.dispatchEvent(new WheelEvent('wheel',{bubbles:true,deltaY:-20}));
    props.code = '';await update();expect(container.querySelector('pre')).toBeNull();
    props.code = 'new revision';await update();expect(container.querySelector('pre')!.scrollTop).toBe(0);
  });
});
