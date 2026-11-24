export const APP_DATA_KEY='atoms-app:tasks:v1';
export function validMockData(value:unknown): value is string {
 if(typeof value!=='string'||value.length>100000)return false;
 try{const tasks=JSON.parse(value);return Array.isArray(tasks)&&tasks.length<=500&&tasks.every(t=>t&&typeof t.id==='string'&&t.id.length<=100&&typeof t.title==='string'&&t.title.length<=100&&typeof t.completed==='boolean'&&Object.keys(t).every(k=>['id','title','completed'].includes(k)));}catch{return false;}
}
