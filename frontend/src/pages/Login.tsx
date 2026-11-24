import { useState } from 'react';
import { ArrowUpRight, Atom, Code2, Layers3, LockKeyhole } from 'lucide-react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import { ErrorNotice } from '../components/Modal';

export function AuthBrand() {
  return <section className="auth-brand"><Link className="brand" to="/dashboard"><Atom size={30}/><strong>atoms<span> DEMO</span></strong></Link><div className="brand-copy"><span className="eyebrow">IDEAS INTO POSSIBILITIES</span><h1>你的想法，<br/>值得被创造。</h1><p>从一句需求开始，构建属于你的应用。<br/>登录后连接 DeepSeek，开启你的创作空间。</p><div className="brand-tags"><span><Code2 size={15}/> 描述想法</span><span><Layers3 size={15}/> 生成应用</span><span><LockKeyhole size={15}/> 保存作品</span></div></div><p className="auth-foot">Atoms Demo · 产品原型，不是 Atoms 官方服务 <ArrowUpRight size={14}/></p></section>;
}
function GoogleMark(){
  return <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.39-.18-2.05H12v3.88h5.38a4.61 4.61 0 0 1-2 3.03v2.52h3.24c1.9-1.75 2.98-4.33 2.98-7.38Z"/><path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.62-2.39l-3.24-2.52c-.9.6-2.05.96-3.38.96-2.61 0-4.82-1.76-5.61-4.12H3.05v2.6A10 10 0 0 0 12 22Z"/><path fill="#FBBC05" d="M6.39 13.93A6 6 0 0 1 6.08 12c0-.67.11-1.32.31-1.93v-2.6H3.05A10 10 0 0 0 2 12c0 1.61.38 3.14 1.05 4.53l3.34-2.6Z"/><path fill="#EA4335" d="M12 5.95c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.62 9.62 0 0 0 12 2a10 10 0 0 0-8.95 5.47l3.34 2.6A5.97 5.97 0 0 1 12 5.95Z"/></svg>;
}
export function LoginPage() {
  const { user, meta } = useApp();
  const [params]=useSearchParams();
  const [terms,setTerms]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const authErrors:Record<string,string>={google_not_configured:'Google登录尚未配置',invalid_state:'登录请求已过期或安全校验失败，请重新开始',google_cancelled:'已取消Google授权',google_failed:'Google登录失败，请稍后重试',account_exists:'此Google邮箱对应已有账号，暂不支持自动合并，请使用其他Google账号或联系管理员'};
  const googleStart=async()=>{if(busy||!terms||!meta?.features.google_login)return;setBusy(true);setError('');try{const result=await api<{authorization_url:string}>('/auth/google/start',{method:'POST',body:JSON.stringify({terms_accepted:terms})});if(new URL(result.authorization_url).origin!=='https://accounts.google.com')throw Error('授权目标不受信任');window.location.assign(result.authorization_url);}catch(err){setError(errorText(err));setBusy(false);}};
  if(user)return <Navigate to="/dashboard" replace/>;
  return <div className="auth-layout"><AuthBrand/><main className="auth-main"><div className="auth-card google-login-card"><span className="pill">WELCOME TO ATOMS DEMO</span><h2>欢迎来到你的创作空间</h2><p className="muted">使用 Google 账号登录或注册。<br/>目前仅支持 Google 登录。</p><div className="login-method"><GoogleMark/><span>一个账号，继续你的创作</span></div><label className="check"><input type="checkbox" checked={terms} disabled={busy} onChange={e=>setTerms(e.target.checked)}/>我已阅读并同意演示条款与隐私说明</label><details className="terms"><summary>查看演示条款与隐私说明</summary><p>平台保存账号、项目需求和必要聊天。模型请求由服务器使用你配置的Key执行，Key加密保存，不进入前端、聊天或生成应用。测试、生成与最多3次自动重试可能计费。Mock为独立的开发测试入口，不验证真实身份；共享Mock账号不可输入真实Key或敏感信息。</p></details><ErrorNotice message={error||authErrors[params.get('auth_error')??'']||''}/><button type="button" className="full google-button" disabled={!terms||busy||!meta?.features.google_login} onClick={()=>void googleStart()}>{busy?<span className="spinner"/>:<GoogleMark/>}{busy?'正在前往 Google…':'使用 Google 登录'}{!meta?.features.google_login?' · 待配置':''}</button>{!meta?.features.google_login&&<p className="tiny">Google 登录暂不可用，请稍后重试。</p>}<Link className="text-button login-browse" to="/dashboard">先浏览工作台 <ArrowUpRight size={14}/></Link><p className="tiny login-note"><LockKeyhole size={13}/>登录后连接你的 DeepSeek，项目与模型配置独立保存。</p></div></main></div>;
}
