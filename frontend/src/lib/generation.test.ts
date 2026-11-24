import { describe,expect,it } from 'vitest';
import { applyStream,planContent,runBlocked } from './generation';
import type { Run } from './types';
describe('generation feedback',()=>{
 it('applies stream by run revision and offsets without duplicates',()=>{
  const start={runId:'r',revision:1,offset:0,text:''};
  const delta={run_id:'r',revision:1,offset:0,next_offset:3,delta:'abc',reset:false,stream_bytes:3,status:'generating'};
  const next=applyStream(start,delta);expect(next.text).toBe('abc');expect(applyStream(next,delta).text).toBe('abc');
  expect(applyStream(next,{...delta,revision:2,reset:true,delta:'new'}).text).toBe('new');
 });
 it('distinguishes queued from real generation',()=>{
  const run={status:'queued',requires_resubmit:true} as Run;
  expect(runBlocked(run,null)).toBe(true);
  expect(runBlocked({...run,status:'generating'},null)).toBe(false);
 });
 it('shows structured public plan, not hidden reasoning',()=>{
  expect(planContent('规划助手\n{"scope":"任务管理","components":["表单"],"reasoning":"private"}')).toEqual({summary:'任务管理',items:['表单']});
 });
});
