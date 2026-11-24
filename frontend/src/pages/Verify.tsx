import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { MailCheck } from 'lucide-react';
import { AuthBrand } from './Login';
import { useApp } from '../AppContext';
import { api, errorText } from '../lib/api';
import type { User } from '../lib/types';
import { ErrorNotice } from '../components/Modal';

interface Challenge {challenge_id:string;masked_email:string;expires_at:string;resend_after:string}
export function VerifyPage() {
  const {user,login}=useApp(),navigate=useNavigate();
  const [challengeId,setChallengeId]=useState(()=>sessionStorage.getItem('atoms:challenge'));
  const [challenge,setChallenge]=useState<Challenge|null>(null),[code,setCode]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[clock,setClock]=useState(Date.now());
  useEffect(()=>{if(challengeId)void api<Challenge>(`/auth/challenges/${challengeId}`).then(setChallenge).catch(e=>setError(errorText(e)));const timer=window.setInterval(()=>setClock(Date.now()),1000);return()=>window.clearInterval(timer);},[challengeId]);
  if(user)return <Navigate to="/dashboard" replace/>;
  if(!challengeId)return <Navigate to="/login" replace/>;
  const remaining=challenge?Math.max(0,Math.ceil((Date.parse(challenge.resend_after)-clock)/1000)):0;
  const submit=async(e:React.FormEvent)=>{e.preventDefault();if(busy)return;setBusy(true);setError('');try{const result=await api<{user:User;csrf_token:string}>('/auth/email/verify',{method:'POST',body:JSON.stringify({challenge_id:challengeId,code})});login(result.user,result.csrf_token);sessionStorage.removeItem('atoms:challenge');sessionStorage.removeItem('atoms:login-email');navigate('/dashboard',{replace:true});}catch(err){setError(errorText(err));}finally{setBusy(false);}};
  const resend=async()=>{if(busy||remaining)return;setBusy(true);try{const email=sessionStorage.getItem('atoms:login-email');if(!email)throw new Error('请返回并重新输入邮箱');const result=await api<Challenge>('/auth/email/code',{method:'POST',body:JSON.stringify({email,terms_accepted:true})});sessionStorage.setItem('atoms:challenge',result.challenge_id);setChallengeId(result.challenge_id);setCode('');setChallenge(result);setError('');navigate('/verify-email',{replace:true});}catch(err){setError(errorText(err));}finally{setBusy(false);}};
  return <div className="auth-layout"><AuthBrand/><main className="auth-main"><div className="auth-card"><MailCheck className="purple" size={36}/><h2>检查你的邮箱</h2><p className="muted">请输入发往 <strong>{challenge?.masked_email??'你的邮箱'}</strong> 的验证码。验证码10分钟内有效。</p><form onSubmit={e=>void submit(e)}><label>6 位邮箱验证码<input className="otp" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={e=>setCode(e.target.value.replace(/\D/g,''))} placeholder="—— —— ——" required/></label><ErrorNotice message={error}/><button className="primary full" disabled={busy||code.length!==6||!challenge}>{busy?'验证中…':'验证并继续'}</button></form><div className="verify-actions"><button className="text-button" disabled={busy||remaining>0} onClick={()=>void resend()}>{remaining?`${remaining} 秒后可重发`:'重新发送验证码'}</button><Link to="/login" onClick={()=>{sessionStorage.removeItem('atoms:challenge');sessionStorage.removeItem('atoms:login-email');}}>更换邮箱</Link></div><p className="tiny">未收到邮件？检查垃圾邮件；开发模式请查看本地邮箱文件。</p></div></main></div>;
}
