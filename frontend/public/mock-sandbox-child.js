(() => {
 const channel=document.currentScript.dataset.channel;
 let initial=null,started=false,id=0;
 const pending=new Map();
 const send=message=>parent.postMessage({...message,channel},'*');
 addEventListener('message',event=>{
  if(event.source!==parent||!event.data||event.data.channel!==channel)return;
  const message=event.data;
  if(message.type==='init'&&!started){
   started=true;initial=message.value;
   window.atomsMockStorage={
    getItem:key=>{if(key!=='atoms-app:tasks:v1')throw Error('unsupported key');if(message.error)throw Error('storage unavailable');return initial;},
    setItem:(key,value)=>new Promise((resolve,reject)=>{
     const request=++id;const timer=setTimeout(()=>{pending.delete(request);reject(Error('storage timeout'));},5000);
     pending.set(request,{resolve,reject,timer,value});send({type:'save',id:request,key,value});
    })
   };
   for(const old of document.querySelectorAll('script[type="application/x-atoms-mock"]')){
    const script=document.createElement('script');script.textContent=old.textContent;document.body.append(script);
   }
   send({type:'ready'});
  }else if(message.type==='saved'&&pending.has(message.id)){
   const request=pending.get(message.id);clearTimeout(request.timer);pending.delete(message.id);
   if(message.ok){initial=request.value;request.resolve();}else request.reject(Error('storage rejected'));
  }
 });
 addEventListener('error',()=>send({type:'error'}));
 addEventListener('unhandledrejection',()=>send({type:'error'}));
 addEventListener('DOMContentLoaded',()=>send({type:'init-request'}));
})();
