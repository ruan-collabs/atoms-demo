import { useState } from 'react';
import { ArrowUpRight, Atom, ChevronRight, Code2, Layers3, LockKeyhole } from 'lucide-react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import { ErrorNotice } from '../components/Modal';

export function AuthBrand() {
  return <section className="auth-brand"><Link className="brand" to="/login"><Atom size={30}/><strong>atoms<span> DEMO</span></strong></Link><div className="brand-copy"><span className="eyebrow">IDEAS INTO POSSIBILITIES</span><h1>你的想法，<br/>值得被创造。</h1><p>从一句需求开始，构建属于你的应用。<br/>这是一个持续迭代中的产品基础框架。</p><div className="brand-tags"><span><Code2 size={15}/> React</span><span><Layers3 size={15}/> Python</span><span><LockKeyhole size={15}/> PostgreSQL</span></div></div><p className="auth-foot">Atoms Demo · 产品原型，不是 Atoms 官方服务 <ArrowUpRight size={14}/></p></section>;
}
export function LoginPage() {
  const { user, meta } = useApp(), navigate = useNavigate();
  const [params]=useSearchParams();
  const authErrors:Record<string,string>={google_not_configured:'Google登录尚未配置',invalid_state:'登录请求已过期或安全校验失败，请重新开始',google_cancelled:'已取消Google授权',google_failed:'Google登录失败，请检查网络、OAuth配置后重新开始',account_exists:'此邮箱已有平台账号，请使用邮箱登录；Google绑定需后续双重验证，不会自动合并账号'};
  const googleStart=async()=>{if(busy||!terms)return;setBusy(true);setError('');try{const result=await api<{authorization_url:string}>('/auth/google/start',{method:'POST',body:JSON.stringify({terms_accepted:terms})});const destination=new URL(result.authorization_url);if(destination.origin!=='https://accounts.google.com')throw new Error('授权目标不受信任');window.location.assign(result.authorization_url);}catch(err){setError(errorText(err));setBusy(false);}};
  const [email,setEmail] = useState(''), [terms,setTerms] = useState(false), [busy,setBusy] = useState(false), [error,setError] = useState('');
  if(user) return <Navigate to="/dashboard" replace/>;
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();if(busy)return;setBusy(true);setError('');
    try { const result=await api<{challenge_id:string}>('/auth/email/code',{method:'POST',body:JSON.stringify({email:email.trim(),terms_accepted:terms})});sessionStorage.setItem('atoms:challenge',result.challenge_id);sessionStorage.setItem('atoms:login-email',email.trim());navigate('/verify-email'); }
    catch(err){setError(errorText(err));}finally{setBusy(false);}
  };
  return <div className="auth-layout"><AuthBrand/><main className="auth-main"><div className="auth-card"><span className="pill">WELCOME TO ATOMS DEMO</span><h2>登录或注册</h2><p className="muted">使用 Google 或邮箱继续，开始你的创作之旅。</p><form onSubmit={e=>void submit(e)}><label>邮箱地址<input type="email" autoComplete="email" required maxLength={254} placeholder="you@example.com" value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="check"><input type="checkbox" checked={terms} onChange={e=>setTerms(e.target.checked)}/>我已阅读并同意演示条款与隐私说明</label><details className="terms"><summary>查看演示条款与隐私说明</summary><p>本产品是基础框架，生成和发布功能尚未接入。平台保存邮箱、项目需求和聊天；不要上传敏感数据。模型测试由浏览器直连你选定的服务商，可能产生费用；模型 Key 不上传平台。SMTP 模式发送真实验证码；本地 file 模式只写开发邮箱文件，不向真实邮箱发信。</p></details><ErrorNotice message={error||authErrors[params.get('auth_error')??'']||''}/><button type="button" className="secondary full google-button" disabled={!terms||busy||!meta?.features.google_login} onClick={()=>void googleStart()}>使用 Google 登录{!meta?.features.google_login?' · 待配置':''}</button><p className="tiny">勾选条款后可登录；Google配置缺失时不会跳转或伪造成功。</p>{meta?.mail_mode==='file'&&<div className="info-box">开发模式：验证码写入 .runtime/mailbox.jsonl，不会发送真实邮件。此模式禁止在生产启用。</div>}{meta?.mail_mode==='disabled'&&<div className="info-box">邮箱登录暂不可用，请配置SMTP；Google登录独立于邮件服务。</div>}<button className="primary full" disabled={!terms||!email.trim()||busy||meta?.mail_mode==='disabled'}>{busy?'发送中…':'发送邮箱验证码'}<ChevronRight size={18}/></button></form><p className="tiny">Google 授权后仍需配置模型 · 使用你自己的模型账户</p></div></main></div>;
}
