(() => {
 'use strict';
 const bootstrap=document.currentScript,channel=bootstrap.dataset.channel,buildId=bootstrap.dataset.build,nonce=bootstrap.nonce;
 let started=false,initial=null,requestId=0;
 const pending=new Map();
 const send=message=>parent.postMessage({...message,channel,buildId},'*');
 const valid=value=>{
  if(typeof value!=='string'||value.length>200000)return false;
  try{const data=JSON.parse(value);return data!==null&&typeof data==='object';}catch{return false;}
 };
 window.addEventListener('message',event=>{
  if(event.source!==parent||!event.data||event.data.channel!==channel||event.data.buildId!==buildId)return;
  const message=event.data;
  if(message.type==='init'&&!started){
   started=true;initial=message.value;
   const storage={
    getItem:key=>{if(key!=='atoms-app:data:v1')throw Error('unsupported key');if(message.error)throw Error('storage unavailable');return initial;},
    setItem:(key,value)=>new Promise((resolve,reject)=>{
     if(key!=='atoms-app:data:v1'||!valid(value)||pending.size>=10){reject(Error('invalid application data'));return;}
     const id=++requestId,timer=setTimeout(()=>{pending.delete(id);reject(Error('storage timeout'));},5000);
     pending.set(id,{resolve,reject,timer,value});send({type:'save',id,key,value});
    })
   };
   Object.defineProperty(window,'atomsStorage',{value:Object.freeze(storage),writable:false,configurable:false});
   for(const template of document.querySelectorAll('template[data-atoms-script]')){
    const script=document.createElement('script');script.nonce=nonce;script.textContent=template.content.textContent;document.body.append(script);template.remove();
   }
   document.dispatchEvent(new Event('DOMContentLoaded'));
   send({type:'ready'});
  } else if(message.type==='saved'&&pending.has(message.id)){
   const item=pending.get(message.id);clearTimeout(item.timer);pending.delete(message.id);
   if(message.ok){initial=item.value;item.resolve();}else item.reject(Error('storage rejected'));
  }
 });
 addEventListener('error',()=>send({type:'error'}));
 addEventListener('unhandledrejection',()=>send({type:'error'}));
 addEventListener('DOMContentLoaded',()=>send({type:'init-request'}));
})();
