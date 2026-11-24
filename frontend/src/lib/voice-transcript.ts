export interface Transcript {type:string;seq:number;text:string;final:boolean;replace?:boolean}
export function applyTranscript(state:{seq:number;committed:string;interim:string},event:Transcript){
  if(event.type!=='transcript'||!Number.isInteger(event.seq)||event.seq<=state.seq||typeof event.text!=='string'||typeof event.final!=='boolean')return state;
  const text=event.text.slice(0,4000);
  if(event.replace)return {seq:event.seq,committed:event.final?text:'',interim:event.final?'':text};
  return {seq:event.seq,committed:event.final?(state.committed+' '+text).trim().slice(0,4000):state.committed,interim:event.final?'':text};
}
export const transcriptText=(state:{committed:string;interim:string})=>(state.committed+' '+state.interim).trim().slice(0,4000);
