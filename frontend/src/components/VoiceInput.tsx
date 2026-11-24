import { useEffect, useRef, useState } from 'react';
import { Mic, Square } from 'lucide-react';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import { applyTranscript, transcriptText } from '../lib/voice-transcript';
interface VoiceStatus {enabled:boolean;provider?:string;provider_name?:string;max_seconds:number;message:string}
export function VoiceInput({value,onChange,disabled=false,onListeningChange}:{value:string;onChange:(value:string)=>void;disabled?:boolean;onListeningChange?:(value:boolean)=>void}){
 const {user}=useApp();const [status,setStatus]=useState<VoiceStatus|null>(null),[listening,setListening]=useState(false),[error,setError]=useState(''),[partial,setPartial]=useState('');
 const [starting,setStarting]=useState(false),[finishing,setFinishing]=useState(false);
 const resources=useRef<{socket?:WebSocket;stream?:MediaStream;context?:AudioContext;node?:AudioWorkletNode;timer?:number;stopping?:boolean}>({});
 const transcript=useRef({seq:0,committed:'',interim:''}),base=useRef(''),latest=useRef(onChange),listener=useRef(onListeningChange),cancelled=useRef(false);
 latest.current=onChange;listener.current=onListeningChange;
 const audioOff=()=>{const r=resources.current;r.stream?.getTracks().forEach(t=>t.stop());r.node?.disconnect();if(r.context)void r.context.close().catch(()=>{});r.stream=undefined;r.node=undefined;r.context=undefined;};
 const release=()=>{const r=resources.current;audioOff();window.clearTimeout(r.timer);resources.current={};r.socket?.close();setStarting(false);setListening(false);setFinishing(false);setPartial('');listener.current?.(false);};
 const stop=()=>{
  cancelled.current=true;const r=resources.current;if(r.stopping)return;r.stopping=true;audioOff();window.clearTimeout(r.timer);setListening(false);
  if(r.socket?.readyState===WebSocket.OPEN){
   setFinishing(true);listener.current?.(true);r.socket.send(JSON.stringify({type:'stop'}));
   r.timer=window.setTimeout(()=>{if(status?.provider==='pipecat-volcengine')setError('语音收尾超时，请检查已转写文字后手动重试');release();},status?.provider==='pipecat-volcengine'?7000:1500);
  }else release();
 };
 useEffect(()=>{void api<VoiceStatus>('/voice/status').then(setStatus).catch(()=>setStatus({enabled:false,max_seconds:60,message:'语音状态暂不可用'}));return()=>{cancelled.current=true;const r=resources.current;r.stream?.getTracks().forEach(t=>t.stop());r.node?.disconnect();if(r.context)void r.context.close().catch(()=>{});window.clearTimeout(r.timer);resources.current={};r.socket?.close();};},[]);
 useEffect(()=>{if(!user&&(resources.current.stream||resources.current.socket)){cancelled.current=true;release();}},[user?.id]);
 const start=async()=>{
  if(!user||!status?.enabled||disabled||starting||listening||finishing)return;
  setError('');cancelled.current=false;base.current=value;transcript.current={seq:0,committed:'',interim:''};
  try{
   if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia||!window.AudioWorkletNode)throw Error('当前浏览器不支持安全语音输入，请使用HTTPS和支持AudioWorklet的浏览器');
   if(!window.confirm(`开始语音输入后，音频会通过平台发送至${status.provider_name??'语音服务'}转写，可能产生费用。不保存原始音频；转写仅填入输入框，不自动发送需求。是否开始？`))return;
   setStarting(true);listener.current?.(true);
   const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});
   if(cancelled.current){stream.getTracks().forEach(t=>t.stop());return;}
   const context=new AudioContext();const r={stream,context} as typeof resources.current;resources.current=r;await context.audioWorklet.addModule('/voice-worklet.js');
   if(cancelled.current||resources.current!==r)return;
   const node=new AudioWorkletNode(context,'atoms-pcm-input');r.node=node;
   const gain=context.createGain();gain.gain.value=0;context.createMediaStreamSource(stream).connect(node).connect(gain).connect(context.destination);
   const url=new URL('/api/voice/ws',window.location.origin);url.protocol=url.protocol==='https:'?'wss:':'ws:';
   const socket=new WebSocket(url);r.socket=socket;
   r.timer=window.setTimeout(()=>{setError('语音连接超时');release();},15000);
   socket.onmessage=event=>{if(resources.current!==r)return;try{
    const msg=JSON.parse(event.data);
    if(msg.type==='ready'){
     if(r.stopping)return;window.clearTimeout(r.timer);setStarting(false);setListening(true);listener.current?.(true);r.timer=window.setTimeout(stop,status.max_seconds*1000);
     node.port.onmessage=e=>{if(resources.current!==r||r.stopping)return;if(socket.readyState===WebSocket.OPEN&&socket.bufferedAmount<64000)socket.send(e.data);else if(socket.bufferedAmount>=64000){setError('语音网络拥塞，已停止，请手动重试');stop();}};
    }else if(msg.type==='transcript'){
     transcript.current=applyTranscript(transcript.current,msg);setPartial(transcript.current.interim);latest.current((base.current+' '+transcriptText(transcript.current)).trim().slice(0,4000));
    }else if(msg.type==='done')release();
    else if(msg.type==='error'){setError(msg.message||'语音服务不可用');release();}
   }catch{setError('语音响应异常');release();}};
   socket.onerror=()=>{if(resources.current===r){setError('语音连接失败；请确认登录、服务凭证和网络');release();}};
   socket.onclose=()=>{if(resources.current===r)release();};
   await context.resume();
  }catch(e){setError(errorText(e));release();}
 };
 return <div className="voice-input"><button type="button" className="secondary" disabled={finishing||disabled||!user||!status?.enabled} onClick={()=>listening||starting?stop():void start()} aria-label={listening||starting?'停止语音输入':'开始语音输入'}>
{listening||starting?<Square size={15}/>:<Mic size={15}/>} {finishing?'收尾中…':listening?'停止转写':starting?'取消连接':'语音输入'}</button><span className="tiny" role="status">{error||(!user?'登录后可用语音输入':finishing?'正在接收最后的转写结果…':listening?(partial?'实时转写中…':'正在聆听…'):status?.message||'读取语音配置…')}</span></div>;
}
