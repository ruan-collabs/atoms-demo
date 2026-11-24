import {useEffect,useMemo,useRef,useState} from 'react';
import {APPLICATION_DATA_KEY,validApplicationData} from '../lib/application-sandbox';
export function ApplicationPreview({projectId,buildId,ownerId,publicView=false,reload=0}:{projectId:string;buildId:string;ownerId:string;publicView?:boolean;reload?:number}){
 const frame=useRef<HTMLIFrameElement>(null);
 const channel=useMemo(()=>crypto.randomUUID(),[projectId,buildId,reload]);
 const storageKey=`atoms:app-data:${publicView?'public':ownerId}:${projectId}:${publicView?'public':'preview'}:v1`;
 const [status,setStatus]=useState('沙箱加载中…');
 useEffect(()=>{
  let initialized=false,ready=false,lastId=0,saves=0,windowStart=Date.now();setStatus('沙箱加载中…');
  const send=(value:object)=>frame.current?.contentWindow?.postMessage({...value,channel,buildId},'*');
  const listen=(event:MessageEvent)=>{
   if(event.source!==frame.current?.contentWindow||event.origin!=='null'||!event.data||event.data.channel!==channel||event.data.buildId!==buildId)return;
   const message=event.data;
   if(message.type==='init-request'&&!initialized){initialized=true;try{const value=localStorage.getItem(storageKey);if(value!==null&&!validApplicationData(value))throw Error();send({type:'init',value});}catch{send({type:'init',value:null,error:true});setStatus('存储不可用或原数据损坏，未清除原数据');}}
   if(message.type==='ready'&&initialized){ready=true;setStatus('预览已加载 · 无平台权限 · 业务行为待验证');}
   if(message.type==='error')setStatus('应用运行错误；请修改需求或查看代码');
   if(message.type==='save'&&initialized){
    let ok=false;
    if(Date.now()-windowStart>60000){windowStart=Date.now();saves=0;}
    if(Number.isSafeInteger(message.id)&&message.id>lastId&&message.key===APPLICATION_DATA_KEY&&saves<120&&validApplicationData(message.value)){
     lastId=message.id;saves++;
     try{localStorage.setItem(storageKey,message.value);ok=true;}catch{setStatus('数据保存失败，请勿关闭页面');}
    }
    send({type:'saved',id:message.id,ok});
   }
  };
  window.addEventListener('message',listen);const timer=setTimeout(()=>{if(!ready)setStatus('沙箱初始化超时，请刷新预览');},15000);
  return()=>{window.removeEventListener('message',listen);clearTimeout(timer);};
 },[channel,buildId,storageKey]);
 const src=`/api/application-sandbox/${projectId}/frame?channel=${encodeURIComponent(channel)}&build_id=${buildId}${publicView?'&public_view=true':''}`;
 return <><span className="preview-status tiny" role="status">{status}</span><iframe key={channel} title="生成应用预览" ref={frame} src={src} sandbox="allow-scripts allow-forms" referrerPolicy="no-referrer" className="app-frame"/></>;
}
