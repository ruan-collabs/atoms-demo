import { useEffect, useRef, useState } from 'react';
import { Mic, Square } from 'lucide-react';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import { applyTranscript, transcriptText } from '../lib/voice-transcript';
interface VoiceStatus {enabled:boolean;max_seconds:number;message:string}
export function VoiceInput({value,onChange,disabled=false,onListeningChange}:{value:string;onChange:(value:string)=>void;disabled?:boolean;onListeningChange?:(value:boolean)=>void}){
 const {user}=useApp();const [status,setStatus]=useState<VoiceStatus|null>(null),[listening,setListening]=useState(false),[error,setError]=useState(''),[partial,setPartial]=useState('');
 const [starting,setStarting]=useState(false);
 const resources=useRef<{socket?:WebSocket;stream?:MediaStream;context?:AudioContext;node?:AudioWorkletNode;timer?:number}>({});
 const transcript=useRef({seq:0,committed:'',interim:''}),base=useRef(''),latest=useRef(onChange),listener=useRef(onListeningChange),cancelled=useRef(false);
 latest.current=onChange;listener.current=onListeningChange;
 const release=()=>{const r=resources.current;r.stream?.getTracks().forEach(t=>t.stop());r.node?.disconnect();void r.context?.close();window.clearTimeout(r.timer);resources.current={};setStarting(false);setListening(false);listener.current?.(false);};
 const stop=()=>{cancelled.current=true;const socket=resources.current.socket;if(socket?.readyState===WebSocket.OPEN)socket.send(JSON.stringify({type:'stop'}));release();window.setTimeout(()=>socket?.close(),1500);};
 useEffect(()=>{void api<VoiceStatus>('/voice/status').then(setStatus).catch(()=>setStatus({enabled:false,max_seconds:60,message:'语音状态暂不可用'}));return()=>{cancelled.current=true;resources.current.socket?.close();resources.current.stream?.getTracks().forEach(t=>t.stop());resources.current.node?.disconnect();void resources.current.context?.close();window.clearTimeout(resources.current.timer);};},[]);
 useEffect(()=>{if(!user&&(resources.current.stream||resources.current.socket)){stop();setPartial('');}},[user?.id]);
 const start=async()=>{
  if(!user||!status?.enabled||disabled||starting||listening)return;
  setError('');cancelled.current=false;base.current=value;transcript.current={seq:0,committed:'',interim:''};
  try{
   if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia||!window.AudioWorkletNode)throw Error('当前浏览器不支持安全语音输入，请使用HTTPS和支持AudioWorklet的浏览器');
   if(!window.confirm('开始语音输入后，音频会通过平台发送至Deepgram转写，可能产生费用。不保存原始音频；转写仅填入输入框，不自动发送需求。是否开始？'))return;
   setStarting(true);listener.current?.(true);
   const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});
   if(cancelled.current){stream.getTracks().forEach(t=>t.stop());return;}
   const context=new AudioContext();resources.current={stream,context};await context.audioWorklet.addModule('/voice-worklet.js');
   const node=new AudioWorkletNode(context,'atoms-pcm-input');resources.current.node=node;
   const gain=context.createGain();gain.gain.value=0;context.createMediaStreamSource(stream).connect(node).connect(gain).connect(context.destination);
   const url=new URL('/api/voice/ws',window.location.origin);url.protocol=url.protocol==='https:'?'wss:':'ws:';
   const socket=new WebSocket(url);resources.current.socket=socket;
   resources.current.timer=window.setTimeout(()=>{setError('语音连接超时');stop();},15000);
   socket.onmessage=event=>{try{const msg=JSON.parse(event.data);if(msg.type==='ready'){window.clearTimeout(resources.current.timer);setStarting(false);setListening(true);listener.current?.(true);resources.current.timer=window.setTimeout(stop,status.max_seconds*1000);node.port.onmessage=e=>{if(socket.readyState===WebSocket.OPEN&&socket.bufferedAmount<64000)socket.send(e.data);else if(socket.bufferedAmount>=64000){setError('语音网络拥塞，已停止，请手动重试');stop();}};}else if(msg.type==='transcript'){transcript.current=applyTranscript(transcript.current,msg);setPartial(transcript.current.interim);latest.current((base.current+' '+transcriptText(transcript.current)).trim().slice(0,4000));}else if(msg.type==='error'){setError(msg.message||'语音服务不可用');stop();}}catch{setError('语音响应异常');stop();}};
   socket.onerror=()=>{setError('语音连接失败；请确认登录、服务凭证和网络');release();};socket.onclose=()=>{release();setPartial('');};
   await context.resume();
  }catch(e){setError(errorText(e));release();}
 };
 return <div className="voice-input"><button type="button" className="secondary" disabled={starting||disabled||!user||!status?.enabled} onClick={()=>listening?stop():void start()} aria-label={listening?'停止语音输入':'开始语音输入'}>{listening?<Square size={15}/>:<Mic size={15}/>} {listening?'停止转写':'语音输入'}</button><span className="tiny" role="status">{error||(!user?'登录后可用语音输入':listening?(partial?'实时转写中…':'正在聆听…'):status?.message||'读取语音配置…')}</span></div>;
}
