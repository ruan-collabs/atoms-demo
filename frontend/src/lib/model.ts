import { api } from './api';
export interface ModelDraftInput {provider:string;api_key:string;base_url:string;model:string;idempotency_key:string;consent:boolean}
export async function testServerModel(config:ModelDraftInput){
 return api<{draft_id:string;status:string;error:string|null}>('/model-config/test',{method:'POST',body:JSON.stringify(config)});
}
export function safeModelOrigin(baseUrl:string){const url=new URL(baseUrl);if(url.protocol!=='https:'||url.username||url.password||url.search||url.hash)throw Error('无效模型地址');return url.origin;}
