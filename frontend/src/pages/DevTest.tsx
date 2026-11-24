import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import type { User } from '../lib/types';
import { ErrorNotice } from '../components/Modal';
export function DevTestPage(){
 const {user,meta,login}=useApp(),navigate=useNavigate();const [error,setError]=useState(''),[busy,setBusy]=useState(false);
 if(user)return <Navigate to="/dashboard" replace/>;
 if(!meta?.features.mock_auth)return <div className="boot"><h1>开发Mock已禁用</h1></div>;
 const enter=async(account:string)=>{setBusy(true);try{const r=await api<{user:User;csrf_token:string}>('/dev/mock-login',{method:'POST',body:JSON.stringify({account})});login(r.user,r.csrf_token);navigate('/dashboard');}catch(e){setError(errorText(e));}finally{setBusy(false);}};
 return <div className="boot"><span className="pill">仅开发环境 · Mock</span><h1>本地自测入口</h1><p>不验证Google或邮件身份，仅以固定测试账号签发平台测试会话。<br/>生产环境强制关闭，不可用作真实登录验收。</p><ErrorNotice message={error}/><div className="actions"><button className="primary" disabled={busy} onClick={()=>void enter('alice')}>进入测试账号 Alice（Mock）</button><button className="secondary" disabled={busy} onClick={()=>void enter('bob')}>进入测试账号 Bob（Mock）</button></div></div>;
}
