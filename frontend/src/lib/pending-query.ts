const KEY = 'atoms:pending-query:v1';
const MAX_AGE = 30 * 60 * 1000;
export function savePendingQuery(text: string): void {
  const value = text.trim();
  if (!value || value.length > 4000) throw new Error('需求需要1–4000字');
  try { sessionStorage.setItem(KEY, JSON.stringify({ text: value, createdAt: Date.now() })); }
  catch { throw new Error('无法保存待提交需求，请复制文本后登录'); }
}
export function takePendingQuery(): string {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return '';
    sessionStorage.removeItem(KEY);
    const value = JSON.parse(raw);
    if (typeof value.text !== 'string' || !value.text.trim() || value.text.length > 4000 ||
        typeof value.createdAt !== 'number' || Date.now() - value.createdAt > MAX_AGE || value.createdAt > Date.now()) return '';
    return value.text;
  } catch { return ''; }
}
