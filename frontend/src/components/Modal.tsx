import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { X } from 'lucide-react';
import { errorText } from '../lib/api';

export function Modal({ title, onClose, children }: {title: string; onClose: () => void; children: ReactNode}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const node = ref.current;
    const focusable = () => Array.from(node?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),a[href],textarea') ?? []);
    focusable()[0]?.focus();
    const handle = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const items = focusable(), first = items[0], last = items.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', handle);
    return () => { document.removeEventListener('keydown', handle); previous?.focus(); };
  }, [onClose]);
  return <div className="overlay"><div className="modal" role="dialog" aria-modal="true" aria-label={title} ref={ref}><header><h2>{title}</h2><button className="icon-button" aria-label="关闭弹窗" onClick={onClose}><X size={20}/></button></header>{children}</div></div>;
}
export function ErrorNotice({message}: {message: string}) { return message ? <p className="error" role="alert">{message}</p> : null; }
export function RenameModal({name, onClose, onSave}: {name: string; onClose: () => void; onSave: (name: string) => Promise<void>}) {
  const [value, setValue] = useState(name), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  return <Modal title="重命名项目" onClose={onClose}><form onSubmit={async e => {e.preventDefault();setBusy(true);try{await onSave(value.trim());onClose();}catch(err){setError(errorText(err));}finally{setBusy(false);}}}><label>项目名称<input value={value} maxLength={60} onChange={e=>setValue(e.target.value)} required/></label><ErrorNotice message={error}/><footer><button type="button" className="secondary" onClick={onClose} disabled={busy}>取消</button><button className="primary" disabled={busy || !value.trim()}>{busy?'保存中…':'保存名称'}</button></footer></form></Modal>;
}
