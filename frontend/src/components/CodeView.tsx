import { useLayoutEffect, useRef } from 'react';

interface CodeViewProps {
  code: string;
  runId?: string;
  generating: boolean;
  visible: boolean;
  panel: string;
}

export function CodeView({ code, runId, generating, visible, panel }: CodeViewProps) {
  const element = useRef<HTMLPreElement>(null);
  const follow = useRef(true);
  const programmaticTop = useRef<number | null>(null);

  // A new run restores the default; revisions and tab switches do not override manual reading.
  useLayoutEffect(() => {
    follow.current = true;
    programmaticTop.current = null;
  }, [runId]);

  useLayoutEffect(() => {
    const node = element.current;
    if (!node || !visible || !generating || !follow.current || node.clientHeight === 0) return;
    const bottom = Math.max(0, node.scrollHeight - node.clientHeight);
    programmaticTop.current = bottom;
    node.scrollTop = bottom;
  }, [code, runId, generating, visible, panel]);

  const pause = () => { follow.current = false; };
  return !code ? null : <pre ref={element} className="code-view" aria-label="生成的只读代码" tabIndex={0}
    onWheel={event => { if (event.deltaY || event.deltaX) pause(); }}
    onTouchMove={pause}
    onKeyDown={event => {
      if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key)) pause();
    }}
    onScroll={event => {
      if (!visible || !generating || event.currentTarget.clientHeight === 0) return;
      // Native scrollbar dragging also pauses. A queued event from our own write does not.
      if (programmaticTop.current === null || Math.abs(event.currentTarget.scrollTop - programmaticTop.current) > 1) pause();
    }}><code>{code}</code></pre>;
}
