import type { Run, ServiceStatus } from './types';
export const activeStatuses = ['queued', 'planning', 'generating', 'validating', 'cancelling'];
export const statusText: Record<string, string> = {queued:'需求已受理',planning:'整理需求',generating:'生成代码',validating:'安全校验',succeeded:'版本已保存',failed:'生成失败',interrupted:'执行中断',cancelling:'停止中',cancelled:'已停止',save_failed:'保存失败'};
export function runBlocked(run: Run | null | undefined, service: ServiceStatus | null) {
  return !!run && run.status === 'queued' && (!!run.requires_resubmit || service?.worker_ready === false);
}
export function planContent(text: string): {summary:string;items:string[]} | null {
  if (!text.startsWith('规划助手')) return null;
  const raw = text.slice(text.indexOf('\n') + 1).replace(/^```(?:json)?\s*|\s*```$/g,'');
  try {
    const data = JSON.parse(raw);
    const items = ['components','interactions','storage'].flatMap(k => typeof data[k] === 'string' ? [data[k]] : Array.isArray(data[k]) ? data[k].filter((x:unknown)=>typeof x==='string') : []);
    return {summary: typeof data.scope === 'string' ? data.scope : '单页应用范围',items:items.slice(0,8)};
  } catch { return {summary:'本次需求范围',items:[raw.slice(0,2500)]}; }
}
export interface StreamCursor {runId:string;revision:number;offset:number;text:string}
export interface StreamDelta {run_id:string;revision:number;offset:number;next_offset:number;delta:string;reset:boolean;stream_bytes:number;status:string}
export function applyStream(previous:StreamCursor, incoming:StreamDelta):StreamCursor {
  const reset = previous.runId !== incoming.run_id || previous.revision !== incoming.revision || incoming.reset;
  const state = reset ? {runId:incoming.run_id,revision:incoming.revision,offset:0,text:''} : previous;
  if (incoming.offset !== state.offset) return state; // duplicate/out-of-order response
  return {...state,offset:incoming.next_offset,text:(state.text+incoming.delta).slice(0,1_000_000)};
}
