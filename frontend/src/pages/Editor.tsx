import './core-editor.css';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowUp, Check, Code2, Pencil, Rocket, ExternalLink, RefreshCw, Square, Activity, Monitor, Smartphone, AlertTriangle, FileCode2 } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { useApp } from '../AppContext';
import { api, ApiError, errorText } from '../lib/api';
import type { Project, Snapshot, Publication, ServiceStatus } from '../lib/types';
import { activeStatuses, statusText, runBlocked, planContent, applyStream } from '../lib/generation';
import type { StreamCursor, StreamDelta } from '../lib/generation';
import { ErrorNotice, RenameModal, Modal } from '../components/Modal';
import { useDraft } from '../lib/draft';
import { VoiceInput } from '../components/VoiceInput';
import { MockPreview } from '../components/MockPreview';

export function EditorPage() {
  const { projectId } = useParams(), { user, model, refreshModel, meta, setModelOpen } = useApp();
  const [project,setProject]=useState<Project|null>(null), [snapshot,setSnapshot]=useState<Snapshot|null>(null);
  const [publication,setPublication]=useState<Publication|null>(null), [service,setService]=useState<ServiceStatus|null>(null);
  const [loading,setLoading]=useState(true), [error,setError]=useState(''), [syncError,setSyncError]=useState('');
  const [sending,setSending]=useState(false), [renaming,setRenaming]=useState(false), [stopping,setStopping]=useState(false);
  const [publishing,setPublishing]=useState(false), [publishOpen,setPublishOpen]=useState(false), [copied,setCopied]=useState(false);
  const [view,setView]=useState('preview'), [mobilePanel,setMobilePanel]=useState('chat'), [device,setDevice]=useState('desktop');
  const [previewUrl,setPreviewUrl]=useState(''), [previewReady,setPreviewReady]=useState(false), [previewError,setPreviewError]=useState('');
  const [previewReload,setPreviewReload]=useState(0), [buildHtml,setBuildHtml]=useState('');
  const [voiceActive,setVoiceActive]=useState(false), [voiceMessage,setVoiceMessage]=useState('');
  const [draft,setDraft,draftError]=useDraft(`atoms:draft:${user?.id}:${projectId}`), [requestKey,setRequestKey]=useState(()=>crypto.randomUUID());
  const [stream,setStream]=useState<StreamCursor>({runId:'',revision:0,offset:0,text:''});
  const streamRef=useRef(stream), frame=useRef<HTMLIFrameElement>(null), messagesRef=useRef<HTMLDivElement>(null);
  const [newMessages,setNewMessages]=useState(false), manualView=useRef(false), priorBuild=useRef('');
  const run=snapshot?.run, build=snapshot?.build, blocked=runBlocked(run,service);
  const active=!!run&&activeStatuses.includes(run.status)&&!run.requires_resubmit;
  const checkService=useCallback(async()=>{
    try {setService(await api<ServiceStatus>('/projects/generation/service-status'));}
    catch {setService(null);} // unknown is not a false declaration of readiness
  },[]);
  const load=useCallback(async()=>{
    try {
      const [p,s,pub]=await Promise.all([api<Project>(`/projects/${projectId}`),api<Snapshot>(`/projects/${projectId}/snapshot`),api<Publication>(`/projects/${projectId}/publication`)]);
      setProject(p);setSnapshot(s);setPublication(pub);setSyncError('');
    } catch(e) { if(e instanceof ApiError&&e.status===404)setError(errorText(e)); else setSyncError('连接恢复中；不会自动重发模型请求'); }
    finally {setLoading(false);}
  },[projectId]);
  useEffect(()=>{let alive=true;const poll=async()=>{await load();if(alive)timer=window.setTimeout(poll,1200);};let timer=0;void poll();return()=>{alive=false;clearTimeout(timer);};},[load]);
  useEffect(()=>{void checkService();const timer=setInterval(()=>void checkService(),5000);return()=>clearInterval(timer);},[checkService,model?.version]);
  useEffect(()=>{
    let alive=true,timer=0;
    const initial={runId:run?.id??'',revision:0,offset:0,text:''};streamRef.current=initial;setStream(initial);
    if(!run?.id)return;
    const poll=async()=>{
      try {
        const current=streamRef.current;
        const delta=await api<StreamDelta>(`/projects/${projectId}/runs/${run.id}/stream?offset=${current.offset}&revision=${current.revision}`);
        if(!alive)return;
        const next=applyStream(streamRef.current,delta);streamRef.current=next;setStream(next);
      } catch { /* existing snapshot surfaces connection problems */ }
      if(alive)timer=window.setTimeout(poll,700);
    };
    void poll();return()=>{alive=false;clearTimeout(timer);};
  },[projectId,run?.id]);
  useEffect(()=>{
    if(run?.status==='generating'&&!build&&!manualView.current)setView('code');
    if(blocked&&!build&&!manualView.current)setView('activity');
    if(build?.id!==priorBuild.current){priorBuild.current=build?.id??'';if(build&&!manualView.current)setView('preview');}
  },[run?.status,blocked,build?.id]);
  useEffect(()=>{
    if(!build)return;let alive=true;setPreviewReady(false);setPreviewError('');setPreviewUrl('');
    void api<{html:string}>(`/projects/${projectId}/build`).then(r=>{if(alive)setBuildHtml(r.html);}).catch(e=>{if(alive)setPreviewError(errorText(e));});
    if(build.mock&&meta?.features.mock_sandbox)setPreviewUrl(`/mock-preview/${projectId}`);
    else void api<{url:string}>(`/projects/${projectId}/preview-link`).then(r=>{if(alive)setPreviewUrl(r.url);}).catch(e=>{if(alive)setPreviewError(errorText(e));});
    return()=>{alive=false;};
  },[projectId,build?.id,previewReload,meta?.features.mock_sandbox,service?.preview_ready]);
  useEffect(()=>{
    if(!previewUrl||build?.mock&&meta?.features.mock_sandbox)return;
    let ready=false;
    const listener=(event:MessageEvent)=>{
      if(event.source!==frame.current?.contentWindow||event.origin!==new URL(previewUrl).origin||event.data?.build_id!==build?.id)return;
      if(event.data.type==='atoms-preview-ready'){ready=true;setPreviewReady(true);setPreviewError('');}
      if(event.data.type==='atoms-preview-error')setPreviewError('应用运行错误；结构校验不代表业务全部通过');
    };
    window.addEventListener('message',listener);
    const timer=setTimeout(()=>{if(!ready)setPreviewError('预览初始化超过15秒，请重载当前构建');},15000);
    return()=>{window.removeEventListener('message',listener);clearTimeout(timer);};
  },[previewUrl,build?.id,build?.mock,meta?.features.mock_sandbox]);
  useEffect(()=>{const node=messagesRef.current;if(!node)return;if(node.scrollHeight-node.scrollTop-node.clientHeight<150)node.scrollTop=node.scrollHeight;else setNewMessages(true);},[snapshot?.messages.length]);
  const selectView=(value:string)=>{manualView.current=true;setView(value);};
  const update=(value:string)=>{setDraft(value);setRequestKey(crypto.randomUUID());};
  const send=async()=>{
    if(sending||voiceActive||active||!model||!draft.trim()||service?.can_generate===false)return;
    setSending(true);setError('');
    try {await api(`/projects/${projectId}/generate`,{method:'POST',body:JSON.stringify({prompt:draft.trim(),idempotency_key:requestKey,config_id:model.id,config_version:model.version,base_build_id:build?.id??null})});setDraft('');setRequestKey(crypto.randomUUID());manualView.current=false;await load();}
    catch(e){setError(errorText(e));if(e instanceof ApiError&&e.status===428)await refreshModel();await checkService();}
    finally{setSending(false);}
  };
  const retry=async()=>{
    if(!run||!model||sending||service?.can_generate===false)return;setSending(true);setError('');
    try{await api(`/projects/${projectId}/runs/${run.id}/retry`,{method:'POST',body:JSON.stringify({idempotency_key:requestKey,config_id:model.id,config_version:model.version})});setRequestKey(crypto.randomUUID());manualView.current=false;await load();}
    catch(e){setError(errorText(e));}finally{setSending(false);}
  };
  const stop=async()=>{if(!run)return;try{await api(`/projects/${projectId}/runs/${run.id}/stop`,{method:'POST'});setStopping(false);await load();}catch(e){setError(errorText(e));}};
  const publish=async()=>{if(!build)return;setPublishing(true);try{await api(`/projects/${projectId}/publish`,{method:'POST',body:JSON.stringify({build_id:build.id,idempotency_key:requestKey})});setRequestKey(crypto.randomUUID());await load();}catch(e){setError(errorText(e));}finally{setPublishing(false);}};
  const closePublish=useCallback(()=>setPublishOpen(false),[]),closeStop=useCallback(()=>setStopping(false),[]);
  if(loading)return <main className="editor-loading">正在恢复项目、消息和后台任务…</main>;
  if(!project)return <main className="editor-loading"><ErrorNotice message={error||syncError}/><button className="secondary" onClick={()=>void load()}>重试加载</button><Link to="/projects">返回项目列表</Link></main>;
  const code=active&&stream.text?stream.text:buildHtml||stream.text;
  const label=blocked?'尚未开始生成':run?statusText[run.status]:'需求已保存';
  const allowPublish=!!build&&!active&&!!service?.preview_ready&&!!service?.publication_ready;
  return <main className="editor core-editor">
    <header className="editor-header"><Link className="icon-button" to="/projects" aria-label="返回项目列表"><ArrowLeft size={18}/></Link><h2>{project.name}</h2><button className="icon-button" aria-label="重命名项目" onClick={()=>setRenaming(true)}><Pencil size={15}/></button><span className={`build-state ${blocked?'is-blocked':''}`}><span className="status-dot"/>{label}</span><button className="model-action" onClick={()=>setModelOpen(true)}>{model?.provider??'模型设置'}</button><button className="secondary publish" disabled={!allowPublish} title={allowPublish?'发布当前成功版本':'需要成功构建与可用发布服务'} onClick={()=>setPublishOpen(true)}><Rocket size={15}/>{publication?.published_build_id?'更新发布':'发布'}</button></header>
    <div className="mobile-tabs"><button className={mobilePanel==='chat'?'selected':''} onClick={()=>setMobilePanel('chat')}>需求</button><button className={mobilePanel==='workspace'?'selected':''} onClick={()=>setMobilePanel('workspace')}>工作区</button></div>
    <div className={`editor-panels tab-${mobilePanel}`}>
      <section className="chat-panel"><div className="panel-heading">需求对话 <span className="pill">{model?.mock?'开发Mock':'真实模型'}</span></div><ErrorNotice message={syncError}/>
        <div className="messages" ref={messagesRef}>{snapshot?.messages.map(m=>{
          const plan=planContent(m.content);
          return <article className={`message ${m.role} ${plan?'scope-card':''}`} key={m.id}><div className="message-meta"><span>{m.role==='user'?'你':plan?'本次构建':'构建助手'}</span><time>{new Date(m.created_at).toLocaleTimeString()}</time></div>{plan?<><strong>{plan.summary}</strong><ul>{plan.items.map((item,index)=><li key={index}>{item}</li>)}</ul></>:<p>{m.content}</p>}</article>;
        })}
        {run&&<section className={`build-card ${blocked?'blocked-card':''}`} aria-label="本次构建状态"><h3>{label}{run.mock?' [Mock]':''}</h3>{blocked?<><p>需求已保留，当前不能开始生成。</p><button className="text-button" onClick={()=>void checkService()}>检查服务</button>{run.requires_resubmit&&<button className="secondary" disabled={sending||!service?.can_generate} onClick={()=>void retry()}>重新提交（可能计费）</button>}</>:<ol className="stage-list">{['planning','generating','validating','succeeded'].map((stage,index)=>{const current=['planning','generating','validating','succeeded'].indexOf(run.status),done=current>index||run.status==='succeeded',working=current===index&&active;return <li key={stage} className={done?'done':working?'working':''}>{done?<Check size={14}/>:working?<span className="spinner"/>:<span className="stage-dot"/>}<span>{statusText[stage]}</span></li>;})}</ol>}{run.status==='succeeded'&&<><p>结构与脚本校验通过；业务行为请在预览中验证。</p><button className="primary full" onClick={()=>{selectView('preview');setMobilePanel('workspace');}}>在预览中试用</button><div className="suggestions"><button onClick={()=>update('改成深色主题，保留现有功能与数据')}>改成深色主题</button><button onClick={()=>update('增加搜索功能，保留现有数据')}>增加搜索</button></div></>}</section>}
        <ErrorNotice message={run?.error??''}/></div>
        {newMessages&&<button className="text-button" onClick={()=>{if(messagesRef.current)messagesRef.current.scrollTop=messagesRef.current.scrollHeight;setNewMessages(false);}}>查看新消息</button>}
        <div className="chat-input"><ErrorNotice message={error||draftError}/>{active&&<button className="text-button" disabled={run?.status==='cancelling'} onClick={()=>setStopping(true)}><Square size={12}/> 停止生成</button>}{run&&['failed','cancelled','interrupted'].includes(run.status)&&<button className="text-button" disabled={sending||!service?.can_generate} onClick={()=>void retry()}>重试当前需求（可能计费）</button>}{run?.status==='save_failed'&&<button className="text-button" onClick={()=>void api(`/projects/${projectId}/runs/${run.id}/retry-save`,{method:'POST'}).then(load).catch(e=>setError(errorText(e)))}>仅重试保存（不调用模型）</button>}
          <textarea aria-label="修改需求" disabled={voiceActive} value={draft} maxLength={4000} onChange={e=>update(e.target.value)} placeholder={active?'可以先编辑下一条需求…':'描述需要修改的内容…'} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void send();}}}/>
          <div className="prompt-footer"><span className="tiny">{draft.length}/4000 · {active?'构建进行中':build?`基于版本 ${build.number} 修改`:'需求草稿'}</span><VoiceInput value={draft} onChange={update} disabled={sending||active} onListeningChange={setVoiceActive} onStatusChange={setVoiceMessage}/><button className="send-button" aria-label="发送修改需求" disabled={sending||voiceActive||active||!draft.trim()||service?.can_generate===false} onClick={()=>void send()}><ArrowUp size={19}/></button></div>{voiceMessage&&<p className="voice-status tiny" role="status">{voiceMessage}</p>}
        </div>
      </section>
      <section className="preview-panel"><div className="workspace-toolbar"><div className="workspace-tabs" role="tablist" aria-label="工作区视图">{[['preview','预览'],['code','代码'],['activity','活动']].map(([value,text])=><button role="tab" aria-selected={view===value} className={view===value?'selected':''} key={value} onClick={()=>selectView(value)}>{text}</button>)}</div><div className="actions"><span className="tiny">{build?`版本 ${build.number}${active?' · 上一成功构建':''}`:'暂无版本'}</span><button className={`icon-button ${device==='desktop'?'selected':''}`} aria-label="桌面预览" onClick={()=>setDevice('desktop')}><Monitor size={15}/></button><button className={`icon-button ${device==='mobile'?'selected':''}`} aria-label="手机预览" onClick={()=>setDevice('mobile')}><Smartphone size={15}/></button><button className="icon-button" disabled={!build} aria-label="刷新预览" onClick={()=>setPreviewReload(previewReload+1)}><RefreshCw size={15}/></button>{previewUrl&&<a className="icon-button" aria-label="独立打开预览" href={previewUrl} target="_blank" rel="noreferrer"><ExternalLink size={15}/></a>}</div></div>
        <div className={`preview-surface device-${device}`} hidden={view!=='preview'}><ErrorNotice message={previewError}/>{build?.mock&&meta?.features.mock_sandbox&&buildHtml&&user?<MockPreview html={buildHtml} projectId={projectId!} ownerId={user.id} reload={previewReload}/>:previewUrl?<><span className="preview-status tiny" role="status">{previewReady?'预览已加载 · 业务行为待验证':'预览加载中…'}</span><iframe key={previewUrl+previewReload} title="生成应用预览" ref={frame} src={previewUrl} sandbox="allow-scripts allow-same-origin allow-forms" referrerPolicy="no-referrer" className="app-frame"/></>:<div className="preview-empty"><Code2 size={40}/><h2>{blocked?'生成服务未就绪':active?'应用尚未就绪':'暂无成功构建'}</h2><p>{blocked?'需求已保留，服务恢复后需手动提交。':'完整代码校验并保存后，将在这里运行。'}</p><button className="secondary" onClick={()=>selectView(blocked?'activity':'code')}>{blocked?'查看服务状态':'查看构建代码'}</button></div>}</div>
        <div className="code-workspace" hidden={view!=='code'}><div className="code-heading"><FileCode2 size={15}/> index.html <span>{run?.status==='generating'?'正在接收代码':code?'只读代码':'等待代码'}</span><small>{run?.stream_bytes?`已接收 ${(run.stream_bytes/1024).toFixed(1)} KB`:''}</small></div>{code?<pre className="code-view" aria-label="生成的只读代码"><code>{code}</code></pre>:<div className="preview-empty"><FileCode2 size={36}/><h2>{blocked?'尚未开始生成':'等待模型返回代码'}</h2><p>不会显示假代码，也不会执行流式半成品。</p></div>}<div className="activity-footer"><Activity size={14}/>{run?.events.at(-1)?.detail??'需求已保存'}</div></div>
        <div className="activity-workspace" hidden={view!=='activity'}>{(blocked||service?.can_generate===false)&&<section className="service-empty"><AlertTriangle size={30}/><h2>生成服务未就绪</h2><p>你的需求已保留，无需重复发送。恢复后手动提交。</p><div className="actions"><button className="primary" onClick={()=>void checkService()}>检查服务</button><Link className="secondary" to="/dashboard">返回工作台</Link></div></section>}<section className="service-card"><h3>服务状态</h3><p>模型配置 <span>{model?'已保存':'未配置'}</span></p><p>执行器 <span>{service?service.worker_ready?'可用':'未就绪':'待核实'}</span></p><p>隔离预览服务 <span>{service?service.preview_ready?'可用':'未就绪':'待核实'}</span></p></section><section className="event-list"><h3>构建活动</h3>{run?.events.map(event=><div className="event-row" key={event.seq}><span className="stage-dot"/><strong>{statusText[event.stage]??event.stage}</strong><p>{event.detail}</p><time>{new Date(event.time).toLocaleTimeString()}</time></div>)}</section></div>
      </section>
    </div>
    {renaming&&<RenameModal name={project.name} onClose={()=>setRenaming(false)} onSave={async name=>{await api(`/projects/${projectId}`,{method:'PATCH',body:JSON.stringify({name})});await load();}}/>}
    {stopping&&<Modal title="停止生成？" onClose={closeStop}><p>停止后保留上次成功构建。供应商已产生的费用可能无法撤回。</p><footer><button className="secondary" onClick={closeStop}>继续生成</button><button className="primary" onClick={()=>void stop()}>确认停止</button></footer></Modal>}
    {publishOpen&&<Modal title="发布应用" onClose={closePublish}><p>当前版本 {build?.number} · {build?.mock?'开发Mock产物':'结构与脚本校验通过'}</p><div className="info-box">公开访客不需要模型Key。预览数据不迁移到发布环境；本地链接不是公网部署。</div><p>发布状态：{publication?.status}{publication?.has_changes?' · 有未发布更改':''}</p><ErrorNotice message={publication?.error??''}/>{publication?.url&&<><label>实际访问链接<input readOnly value={publication.url}/></label><div className="actions"><button className="secondary" onClick={()=>void navigator.clipboard.writeText(publication.url!).then(()=>setCopied(true)).catch(()=>setError('剪贴板不可用，请手动选择链接'))}>{copied?'已复制':'复制链接'}</button><a className="secondary" href={publication.url} target="_blank" rel="noreferrer">打开公开应用</a></div></>}<footer><button className="secondary" onClick={closePublish}>关闭</button><button className="primary" disabled={publishing||['publishing','updating'].includes(publication?.status??'')} onClick={()=>void publish()}>{publication?.published_build_id?'更新线上版本':'确认发布'}</button></footer></Modal>}
  </main>;
}
