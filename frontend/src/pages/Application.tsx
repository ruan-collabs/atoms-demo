import {useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {api,errorText} from '../lib/api';
import {useApp} from '../AppContext';
import {ApplicationPreview} from '../components/ApplicationPreview';
export function ApplicationPage({publicView=false}:{publicView?:boolean}){
 const {projectId}=useParams(),{user}=useApp();
 const [build,setBuild]=useState<{id:string;number:number}|null>(null),[error,setError]=useState('');
 useEffect(()=>{let alive=true;setError('');setBuild(null);
  if(!publicView&&!user){setError('请登录后预览私人应用');return;}
  void api<{id:string;number:number}>(publicView?`/application-sandbox/${projectId}/public`:`/projects/${projectId}/build`).then(r=>{if(alive)setBuild(r);}).catch(e=>{if(alive)setError(errorText(e));});return()=>{alive=false;};
 },[projectId,user?.id,publicView]);
 return <main className="mock-app-page"><header><strong>{publicView?'公开应用':'独立预览'}</strong><span className="tiny">版本 {build?.number??'—'} · 数据仅保存在当前浏览器</span><Link to="/dashboard">返回平台</Link></header>{error?<p className="error">{error}</p>:build?<ApplicationPreview projectId={projectId!} buildId={build.id} ownerId={user?.id??'public'} publicView={publicView}/>:<p>正在读取已保存构建…</p>}</main>;
}
