import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import { AppProvider, useApp } from './AppContext';
import { ProtectedLayout } from './components/Layout';
import { ErrorNotice } from './components/Modal';
import { DashboardPage } from './pages/Dashboard';
import { EditorPage } from './pages/Editor';
import { LoginPage } from './pages/Login';
import { ProjectsPage } from './pages/Projects';
import { VerifyPage } from './pages/Verify';
import { DevTestPage } from './pages/DevTest';
import { MockAppPage } from './pages/MockApp';

function AppRoutes() {
  const {loading,loadError,restore}=useApp();
  if(loading)return <div className="boot"><span className="spinner"/><p>正在连接你的工作区…</p></div>;
  if(loadError)return <div className="boot"><h2>暂时无法连接平台</h2><ErrorNotice message={loadError}/><button className="primary" onClick={()=>void restore()}>重试连接</button></div>;
  return <Routes><Route path="/mock-apps/:projectId" element={<MockAppPage publicView/>}/><Route path="/mock-preview/:projectId" element={<MockAppPage/>}/><Route path="/dev-test" element={<DevTestPage/>}/><Route path="/" element={<Navigate to="/dashboard" replace/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/verify-email" element={<VerifyPage/>}/><Route element={<ProtectedLayout/>}><Route path="/dashboard" element={<DashboardPage/>}/><Route path="/projects" element={<ProjectsPage/>}/><Route path="/projects/:projectId" element={<EditorPage/>}/></Route><Route path="*" element={<div className="boot"><h1>找不到这个页面</h1><Link to="/dashboard">回到工作台</Link></div>}/></Routes>;
}
export default function App() { return <BrowserRouter><AppProvider><AppRoutes/></AppProvider></BrowserRouter>; }
