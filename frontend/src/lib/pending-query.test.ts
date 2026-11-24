import { beforeEach,describe,expect,it } from 'vitest';
import { savePendingQuery,takePendingQuery } from './pending-query';
import { applyTranscript,transcriptText } from './voice-transcript';

beforeEach(()=>sessionStorage.clear());
describe('pending query (no automatic generation)',()=>{
 it('preserves query once across login and then clears',()=>{savePendingQuery('  创建任务板 ');expect(takePendingQuery()).toBe('创建任务板');expect(takePendingQuery()).toBe('');});
 it('rejects empty or oversized text',()=>{expect(()=>savePendingQuery(' ')).toThrow();expect(()=>savePendingQuery('x'.repeat(4001))).toThrow();});
 it('ignores malformed values',()=>{sessionStorage.setItem('atoms:pending-query:v1','not-json');expect(takePendingQuery()).toBe('');});
});
describe('streaming transcripts',()=>{
 it('replaces interim, appends final and ignores duplicate sequences',()=>{
  let s={seq:0,committed:'',interim:''};
  s=applyTranscript(s,{type:'transcript',seq:1,text:'创建',final:false});
  s=applyTranscript(s,{type:'transcript',seq:2,text:'创建任务板',final:false});expect(transcriptText(s)).toBe('创建任务板');
  s=applyTranscript(s,{type:'transcript',seq:3,text:'创建任务板',final:true});
  s=applyTranscript(s,{type:'transcript',seq:3,text:'duplicate',final:true});
  s=applyTranscript(s,{type:'transcript',seq:4,text:'并保存数据',final:true});expect(transcriptText(s)).toBe('创建任务板 并保存数据');
 });
});
