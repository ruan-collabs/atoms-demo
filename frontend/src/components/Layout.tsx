import { useEffect, useState } from 'react';
import { Atom, FolderKanban, House, LogOut, Settings2, ShieldAlert, SquarePlus } from 'lucide-react';
import { NavLink, Navigate, Outlet, useLocation } from 'react-router-dom';
import { useApp } from '../AppContext';
import { ModelModal } from './ModelModal';
import { ErrorNotice } from './Modal';
import { errorText } from '../lib/api';

export function ProtectedLayout() {
  const {user,model,modelOpen,setModelOpen,logout}=useApp();
  const location=useLocation();
  const isPublic=location.pathname==='/dashboard'||location.pathname==='/projects';
  const [menu,setMenu]=useState(false),[error,setError]=useState('');
  useEffect(()=>{if(user&&!model)setModelOpen(true);},[user,model,setModelOpen]);
  if(!user&&!isPublic)return <Navigate to="/dashboard" replace/>;
  return <div className="app-layout">
    <aside className="sidebar">
      <NavLink to="/dashboard" className="brand"><Atom size={28}/><strong>atoms<span> DEMO</span></strong></NavLink>
      <NavLink to="/dashboard" className="new-project"><SquarePlus size={17}/>从新想法开始</NavLink>
      <div className="nav-label">{user?'个人工作区':'访客体验'}</div>
      <nav><NavLink to="/dashboard"><House size={18}/>工作台</NavLink><NavLink to="/projects" end><FolderKanban size={18}/>我的项目</NavLink></nav>
      <div className="sidebar-bottom">
        <div className="version-box"><span className="status-dot"/>应用构建 v0.3.0</div>
        {user?<><button className="account" onClick={()=>setMenu(!menu)}><span className="avatar">{user.email[0].toUpperCase()}</span><span className="account-copy">个人账户<small>{user.email}</small></span></button>
          {menu&&<div className="account-menu"><button onClick={()=>{setModelOpen(true);setMenu(false);}}><Settings2 size={16}/>模型配置</button><button onClick={()=>void logout().catch(err=>setError(errorText(err)))}><LogOut size={16}/>退出登录（后台任务继续）</button></div>}</>
          :<NavLink className="secondary" to="/login">登录 / 注册</NavLink>}
        <ErrorNotice message={error}/>
      </div>
    </aside>
    <div className="app-main">
      <div className="topbar"><span>你的创作空间 <span className="muted">/ {user?'PERSONAL':'GUEST'}</span></span>
        {user?<><button className={model?'model-chip enabled':'model-chip'} onClick={()=>setModelOpen(true)}><Settings2 size={15}/>{model?`${model.provider} · ${model.model}`:'需要配置模型'}</button><button className="mobile-account icon-button" aria-label="退出登录" onClick={()=>void logout().catch(err=>setError(errorText(err)))}><LogOut size={16}/></button></>:<NavLink className="secondary" to="/login">登录</NavLink>}
      </div>
      {!user||model||isPublic?<Outlet/>:<main className="gate"><ShieldAlert size={45}/><h1>先连接你的模型，<br/>再开始创造。</h1><p>配置并测试后解锁生成。私有接口始终鉴权，不因页面可浏览而开放。</p><button className="primary" onClick={()=>setModelOpen(true)}>配置模型</button></main>}
    </div>
    {user&&modelOpen&&<ModelModal key={user.id}/>}
  </div>;
}
