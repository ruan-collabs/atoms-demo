import { useEffect,useMemo,useRef,useState } from 'react';
import { APP_DATA_KEY,validMockData } from '../lib/mock-sandbox';
export function MockPreview({html,projectId,ownerId,reload=0,publicView=false}:{html:string;projectId:string;ownerId:string;reload?:number;publicView?:boolean}){
 const frame=useRef<HTMLIFrameElement>(null);const channel=useMemo(()=>crypto.randomUUID(),[projectId,html,reload]);
 const frameUrl=`/api/mock-sandbox/${projectId}/frame?channel=${encodeURIComponent(channel)}${publicView?'&public_view=true':''}`;
 const storageKey=`atoms:mock-app:${publicView?'public':ownerId}:${projectId}:${publicView?'public':'preview'}:v1`;
 const [status,setStatus]=useState('沙箱初始化中…');
 useEffect(()=>{
  setStatus('沙箱初始化中…');let initialized=false;
  const send=(message:object)=>frame.current?.contentWindow?.postMessage({...message,channel},'*');
  const listen=(event:MessageEvent)=>{
   if(event.source!==frame.current?.contentWindow||event.origin!=='null'||!event.data||event.data.channel!==channel)return;
   const message=event.data;
   if(message.type==='init-request'&&!initialized){initialized=true;try{const raw=localStorage.getItem(storageKey);if(raw!==null&&!validMockData(raw))throw Error();send({type:'init',value:raw});}catch{send({type:'init',value:null,error:true});setStatus('存储不可用或数据损坏，未清除原数据');}}
   if(message.type==='ready')setStatus('Mock沙箱已加载 · 无平台权限');
   if(message.type==='error')setStatus('Mock应用运行错误');
   if(message.type==='save'){
    let ok=false;
    if(message.key===APP_DATA_KEY&&Number.isSafeInteger(message.id)&&message.id>0&&validMockData(message.value)){
     try{localStorage.setItem(storageKey,message.value);ok=true;}catch{setStatus('应用数据保存失败，请勿关闭页面');}
    }
    send({type:'saved',id:message.id,ok});
   }
  };
  window.addEventListener('message',listen);const timer=window.setTimeout(()=>{if(!initialized)setStatus('沙箱加载超时，请刷新预览');},10000);
  return()=>{window.removeEventListener('message',listen);clearTimeout(timer);};
 },[channel,storageKey]);
 return <><span className="tiny" role="status">{status}</span><iframe key={channel} title="生成应用预览" ref={frame} src={frameUrl} sandbox="allow-scripts allow-forms" referrerPolicy="no-referrer" className="app-frame"/></>;
}
