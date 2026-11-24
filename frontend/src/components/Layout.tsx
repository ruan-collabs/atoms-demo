import { useEffect, useState } from 'react';
import { Atom, FolderKanban, House, LogOut, Settings2, ShieldAlert, SquarePlus } from 'lucide-react';
import { NavLink, Navigate, Outlet } from 'react-router-dom';
import { useApp } from '../AppContext';
import { ModelModal } from './ModelModal';
import { ErrorNotice } from './Modal';
import { errorText } from '../lib/api';

export function ProtectedLayout() {
  const {user,model,modelOpen,setModelOpen,logout,meta}=useApp();
  const [menu,setMenu]=useState(false),[error,setError]=useState('');
  useEffect(()=>{if(user&&!model)setModelOpen(true);},[user,model,setModelOpen]);
  if(!user)return <Navigate to="/login" replace/>;
  return <div className="app-layout"><aside className="sidebar"><NavLink to="/dashboard" className="brand"><Atom size={28}/><strong>atoms<span> DEMO</span></strong></NavLink><NavLink to="/dashboard" className="new-project"><SquarePlus size={17}/>从新想法开始</NavLink><div className="nav-label">个人工作区</div><nav><NavLink to="/dashboard"><House size={18}/>工作台</NavLink><NavLink to="/projects" end><FolderKanban size={18}/>我的项目</NavLink></nav><div className="sidebar-bottom"><div className="version-box"><span className="status-dot"/>应用构建 v0.2.0<p>{meta?.features.mock_auth?'开发Mock已启用 · 上线前关闭':'服务端后台执行'}</p></div><button className="account" onClick={()=>setMenu(!menu)}><span className="avatar">{user.email[0].toUpperCase()}</span><span className="account-copy">个人账户<small>{user.email}</small></span></button>{menu&&<div className="account-menu"><button onClick={()=>{setModelOpen(true);setMenu(false);}}><Settings2 size={16}/>模型配置</button><button onClick={()=>void logout().catch(err=>setError(errorText(err)))}><LogOut size={16}/>退出登录（后台任务继续）</button></div>}<ErrorNotice message={error}/></div></aside><div className="app-main"><div className="topbar"><span>你的创作空间 <span className="muted">/ PERSONAL</span></span><button className={model?'model-chip enabled':'model-chip'} onClick={()=>setModelOpen(true)}><Settings2 size={15}/>{model?`${model.provider} · ${model.model}`:'需要配置模型'}</button><button className="mobile-account icon-button" aria-label="退出登录" onClick={()=>void logout().catch(err=>setError(errorText(err)))}><LogOut size={16}/></button></div>{model?<Outlet/>:<main className="gate"><ShieldAlert size={45}/><h1>先连接你的模型，<br/>再开始创造。</h1><p>配置并真实测试 API Key 后解锁项目功能。<br/>关闭弹窗、刷新或访问深链均不会绕过此门禁。</p><button className="primary" onClick={()=>setModelOpen(true)}>配置模型</button><div className="info-box">V1.2：服务器测试并加密保存模型配置。生成、预览、发布使用真实平台链路；开发Mock有明确标签。</div></main>}</div>{modelOpen&&<ModelModal key={user.id}/>}</div>;
}
