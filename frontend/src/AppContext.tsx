import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { api, ApiError, errorText, setCsrf, setUnauthorizedHandler } from './lib/api';
import type { Meta, ModelConfig, User } from './lib/types';
interface Value {
  user:User|null;loading:boolean;loadError:string;meta:Meta|null;model:ModelConfig|null;modelOpen:boolean;
  setModelOpen:(value:boolean)=>void;refreshModel:()=>Promise<void>;
  login:(user:User,csrf:string)=>void;logout:()=>Promise<void>;restore:()=>Promise<void>;
}
const Context=createContext<Value|null>(null);
export function AppProvider({children}:{children:ReactNode}){
  const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true),[loadError,setLoadError]=useState(''),[meta,setMeta]=useState<Meta|null>(null),[model,setModel]=useState<ModelConfig|null>(null),[modelOpen,setModelOpen]=useState(false);
  const refreshModel=useCallback(async()=>{const result=await api<{config:ModelConfig|null}>('/model-config');setModel(result.config);},[]);
  const restore=useCallback(async()=>{setLoading(true);setLoadError('');try{
    setMeta(await api<Meta>('/meta'));const profile=await api<User>('/auth/me');const csrf=await api<{csrf_token:string}>('/auth/csrf');setCsrf(csrf.csrf_token);setUser(profile);
    const result=await api<{config:ModelConfig|null}>('/model-config');setModel(result.config);
    // Remove obsolete V1.1 browser key storage; never read or restore its value.
    try{for(const key of Object.keys(localStorage))if(key.startsWith('atoms:model:'))localStorage.removeItem(key);}catch{/* no browser Key path in V1.2 */}
  }catch(error){setUser(null);setModel(null);setCsrf('');if(!(error instanceof ApiError&&error.status===401))setLoadError(errorText(error));}finally{setLoading(false);}},[]);
  useEffect(()=>{void restore();},[restore]);
  useEffect(()=>{setUnauthorizedHandler(()=>{setUser(null);setModel(null);setCsrf('');});return()=>setUnauthorizedHandler(()=>{});},[]);
  const login=(profile:User,csrf:string)=>{setUser(profile);setCsrf(csrf);setModel(null);void refreshModel().catch(()=>{});};
  const logout=async()=>{await api('/auth/logout',{method:'POST'});setUser(null);setModel(null);setModelOpen(false);setCsrf('');};
  return <Context.Provider value={{user,loading,loadError,meta,model,modelOpen,setModelOpen,refreshModel,login,logout,restore}}>{children}</Context.Provider>;
}
export function useApp(){const value=useContext(Context);if(!value)throw Error('Missing AppProvider');return value;}
