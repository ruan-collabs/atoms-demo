export interface User { id: string; email: string }
export interface Project { id: string; name: string; initial_prompt: string; current_build_id: string | null; created_at: string; updated_at: string; generation_status: string; publication_status: string }
export interface Message { id: string; role: string; content: string; created_at: string }
export interface Meta { version: string; stage: string; mail_mode: 'file'|'smtp'|'disabled'; model_allowed_origins: string[]; features: Record<string, boolean> }
export interface ModelConfig { id:string; provider:string; base_url:string; model:string; version:number; tested_at:string; enabled:boolean; mock:boolean }
export interface Run {id:string;status:string;error:string|null;events:{seq:number;stage:string;detail:string;time:string}[];created_at:string;finished_at:string|null;mock:boolean;retry_of:string|null}
export interface Build {id:string;number:number;validation:Record<string,unknown>;mock:boolean}
export interface Snapshot {run:Run|null;build:Build|null;messages:Message[]}
export interface Publication {status:string;url:string|null;published_build_id:string|null;has_changes:boolean;error:string|null}
