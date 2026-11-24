import { useEffect, useState } from 'react';
import { ArrowUp, ArrowUpRight, Code2, Ellipsis, FolderPlus, Sparkles } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import type { Project } from '../lib/types';
import { ErrorNotice } from '../components/Modal';
import { useDraft } from '../lib/draft';

const examples = [
  {title:'把待办变得轻松', prompt:'创建任务管理应用，支持新增、编辑、删除、完成和筛选任务，数据刷新后保留。',icon:'✦'},
  {title:'展示你的作品', prompt:'创建一个个人作品集页面，展示项目、技能和联系方式，使用简洁的暗色设计。',icon:'◈'},
  {title:'记录生活的灵感', prompt:'创建一个灵感笔记应用，支持标签分类和本地保存。',icon:'✧'},
];
export function ProjectCard({project,action}: {project:Project;action?:()=>void}) {
  return <article className="project-card"><Link to={`/projects/${project.id}`}><div className="project-visual"><Code2 size={30}/><span>{project.current_build_id?'成功构建可预览':'尚无成功构建'}</span></div><div className="project-details"><h3>{project.name}</h3><p>{new Date(project.updated_at).toLocaleString('zh-CN')}</p><div className="card-tags"><span>{project.generation_status}</span><span>{project.publication_status==='published'?'已发布':'未发布'}</span></div></div></Link>{action&&<button className="card-menu icon-button" aria-label={`重命名${project.name}`} onClick={action}><Ellipsis size={20}/></button>}</article>;
}
export function DashboardPage() {
  const {user,model}=useApp(),navigate=useNavigate();
  const draftKey=`atoms:draft:${user?.id}:dashboard`;
  const [prompt,setPrompt,draftError]=useDraft(draftKey);
  const [projects,setProjects]=useState<Project[]>([]),[loading,setLoading]=useState(true),[loadError,setLoadError]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [requestKey,setRequestKey]=useState(()=>crypto.randomUUID());
  const update=(value:string)=>{setPrompt(value);setRequestKey(crypto.randomUUID());};
  const load=()=>{setLoading(true);setLoadError('');void api<{items:Project[]}>('/projects?limit=3').then(r=>setProjects(r.items)).catch(e=>setLoadError(errorText(e))).finally(()=>setLoading(false));};
  useEffect(load,[]);
  const create=async()=>{if(busy||!model||!prompt.trim()||prompt.trim().length>4000)return;setBusy(true);setError('');try{const project=await api<Project>('/projects',{method:'POST',body:JSON.stringify({prompt:prompt.trim(),idempotency_key:requestKey,config_id:model.id,config_version:model.version})});setPrompt('');navigate(`/projects/${project.id}`);}catch(err){setError(errorText(err));}finally{setBusy(false);}};
  return <main className="dashboard"><section className="hero"><span className="eyebrow"><Sparkles size={14}/> ONE IDEA. ENDLESS POSSIBILITIES.</span><h1>你想创造什么？</h1><p>从一个想法开始，把它变成你的下一个作品。</p><div className="prompt-box"><textarea maxLength={4000} value={prompt} onChange={e=>update(e.target.value)} placeholder="描述你想构建的应用、需要的功能和喜欢的风格…" onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void create();}}}/><div className="prompt-footer"><span className="mode"><Code2 size={16}/>项目框架</span><span className="char-count">{prompt.length} / 4000</span><button aria-label="开始生成项目" className="send-button" disabled={busy||!prompt.trim()||!model} onClick={()=>void create()}>{busy?<span className="spinner"/>:<ArrowUp size={20}/>}</button></div></div><ErrorNotice message={error||draftError}/><p className="scope-note">{model?.mock?'当前开发Mock：生成确定性fixture，不调用真实模型、不计费。':'规划、生成及一次修复可能多次计费；后台使用你加密保存的Key。关闭页面不取消任务。'}</p><div className="example-grid">{examples.map(e=><button key={e.title} onClick={()=>update(e.prompt)}><span>{e.icon}</span><strong>{e.title}</strong><ArrowUpRight size={16}/></button>)}</div></section><section className="recent"><div className="section-heading"><h2>最近的项目</h2><Link to="/projects">查看全部 <ArrowUpRight size={15}/></Link></div>{loading?<p className="muted">正在读取你的项目…</p>:loadError?<><ErrorNotice message={loadError}/><button className="secondary" onClick={load}>重试加载</button></>:projects.length?<div className="project-grid">{projects.map(p=><ProjectCard key={p.id} project={p}/>)}</div>:<div className="empty compact"><FolderPlus size={32}/><h3>还没有项目</h3><p>在上方描述想法，保存你的第一个项目。</p></div>}</section></main>;
}
