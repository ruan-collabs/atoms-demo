import { useEffect, useState } from 'react';

export function readDraft(key: string): string {
  try { return localStorage.getItem(key) ?? ''; } catch { return ''; }
}
export function useDraft(key: string): [string, (value: string) => void, string] {
  const [state,setState]=useState(()=>({key,value:readDraft(key)}));
  const [error,setError]=useState('');
  const value=state.key===key?state.value:readDraft(key);
  useEffect(()=>{setState({key,value:readDraft(key)});setError('');},[key]);
  const update=(next:string)=>{
    setState({key,value:next});
    try { if(next)localStorage.setItem(key,next);else localStorage.removeItem(key); }
    catch {setError('本地草稿存储不可用，请不要关闭页面');}
  };
  return [value,update,error];
}
