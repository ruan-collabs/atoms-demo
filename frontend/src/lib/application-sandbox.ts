export const APPLICATION_DATA_KEY='atoms-app:data:v1';
export function validApplicationData(value:unknown):value is string {
 if(typeof value!=='string'||new TextEncoder().encode(value).length>200000)return false;
 try {
  const data=JSON.parse(value);if(data===null||typeof data!=='object')return false;
  let nodes=0;
  const visit=(x:unknown,depth:number):boolean=>{
   if(++nodes>10000||depth>20)return false;
   if(x===null||typeof x==='boolean'||typeof x==='number')return true;
   if(typeof x==='string')return x.length<=50000;
   if(Array.isArray(x))return x.length<=1000&&x.every(item=>visit(item,depth+1));
   if(typeof x==='object')return Object.entries(x).every(([k,v])=>!['__proto__','constructor','prototype'].includes(k)&&k.length<=128&&visit(v,depth+1));
   return false;
  };
  return visit(data,0);
 } catch {return false;}
}
