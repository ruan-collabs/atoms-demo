import { useEffect,useState } from 'react';
import { Link,useParams } from 'react-router-dom';
import { api,errorText } from '../lib/api';
import { useApp } from '../AppContext';
import { MockPreview } from '../components/MockPreview';
export function MockAppPage({publicView=false}:{publicView?:boolean}){
 const {projectId}=useParams(),{user}=useApp();const [build,setBuild]=useState<{html:string;number:number}|null>(null),[error,setError]=useState('');
 useEffect(()=>{let valid=true;setBuild(null);setError('');if(!publicView&&!user){setError('登录后才能独立预览私人项目');return;}
 void api<{html:string;number:number}>(publicView?`/mock-sandbox/${projectId}/public`:`/projects/${projectId}/build`).then(r=>{if(valid)setBuild(r);}).catch(e=>{if(valid)setError(errorText(e));});return()=>{valid=false;};},[projectId,publicView,user?.id]);
 return <main className="mock-app-page"><header><strong>{publicView?'公开Mock应用':'独立Mock预览'}</strong><span className="tiny">示例产物 · 非真实AI生成 · 数据仅存当前浏览器</span><Link to="/dashboard">返回平台</Link></header>{error?<p className="error">{error}</p>:build?<MockPreview html={build.html} projectId={projectId!} ownerId={user?.id??'public'} publicView={publicView}/>:<p>正在加载保存的Mock构建…</p>}</main>;
}
