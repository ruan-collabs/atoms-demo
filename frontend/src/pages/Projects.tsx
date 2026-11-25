import { useEffect, useState } from 'react';
import { ChevronDown, FolderSearch, Search, SquarePlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api, errorText } from '../lib/api';
import type { Project } from '../lib/types';
import { ProjectCard } from './Dashboard';
import { ErrorNotice, RenameModal } from '../components/Modal';
import { useApp } from '../AppContext';
import './projects.css';

export function ProjectsPage() {
  const {user}=useApp();
  const [filter,setFilter]=useState('all');
  const [query,setQuery]=useState(''),[items,setItems]=useState<Project[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[total,setTotal]=useState(0),[hasMore,setHasMore]=useState(false),[renaming,setRenaming]=useState<Project|null>(null),[refresh,setRefresh]=useState(0);
  useEffect(()=>{if(!user){setItems([]);setTotal(0);setHasMore(false);setLoading(false);return;}let active=true;const timer=window.setTimeout(()=>{setLoading(true);setError('');void api<{items:Project[];total:number;has_more:boolean}>(`/projects?status=${filter}&q=${encodeURIComponent(query.trim())}`).then(r=>{if(active){setItems(r.items);setTotal(r.total);setHasMore(r.has_more);}}).catch(e=>{if(active)setError(errorText(e));}).finally(()=>{if(active)setLoading(false);});},250);return()=>{active=false;clearTimeout(timer);};},[query,refresh,filter,user?.id]);
  const more=async()=>{setLoading(true);try{const r=await api<{items:Project[];has_more:boolean}>(`/projects?status=${filter}&q=${encodeURIComponent(query.trim())}&offset=${items.length}`);setItems([...items,...r.items]);setHasMore(r.has_more);}catch(e){setError(errorText(e));}finally{setLoading(false);}};
  if(!user)return <main className="projects-page"><h1>我的项目</h1><p className="muted">你的私人项目只对登录后的账号可见。你可以先在工作台描述想法，发送后再登录。</p><Link className="primary" to="/dashboard">开始描述想法</Link></main>;
  return <main className="projects-page"><div className="page-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h1>我的项目</h1><p className="muted">继续构建，让每个想法都有自己的空间。</p></div><Link className="primary" to="/dashboard"><SquarePlus size={17}/>新建项目</Link></div><div className="list-toolbar"><div className="project-status-filter"><select aria-label="筛选项目状态" value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">全部</option><option value="preview">可预览</option><option value="active">生成中</option><option value="failed">失败</option></select><ChevronDown size={16} aria-hidden="true"/></div><div className="search-field"><Search size={17}/><input aria-label="搜索项目名称" maxLength={60} value={query} onChange={e=>setQuery(e.target.value)} placeholder="搜索项目名称"/></div><span className="muted">{total} 个项目 · 最近更新</span></div><ErrorNotice message={error}/>{error&&<button className="secondary" onClick={()=>setRefresh(refresh+1)}>重试加载</button>}{loading&&!items.length?<p className="muted">项目加载中…</p>:!error&&items.length===0?<div className="empty"><FolderSearch size={42}/><h2>{query?'没有匹配的项目':'你的项目会出现在这里'}</h2><p>{query?'换个关键词，或清除搜索条件。':'创建第一个项目并保存你的想法。'}</p>{query?<button className="secondary" onClick={()=>setQuery('')}>清除搜索</button>:<Link className="primary" to="/dashboard">开始新项目</Link>}</div>:<div className="project-grid">{items.map(p=><ProjectCard key={p.id} project={p} action={()=>setRenaming(p)}/>)}</div>}{hasMore&&<button className="secondary load-more" disabled={loading} onClick={()=>void more()}>{loading?'加载中…':'加载更多'}</button>}{renaming&&<RenameModal name={renaming.name} onClose={()=>setRenaming(null)} onSave={async(name)=>{await api(`/projects/${renaming.id}`,{method:'PATCH',body:JSON.stringify({name})});setRefresh(refresh+1);}}/>}</main>;
}
