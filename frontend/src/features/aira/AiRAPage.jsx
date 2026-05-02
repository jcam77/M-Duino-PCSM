import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BrainCircuit, FileText, RefreshCw, Send, ShieldAlert } from 'lucide-react';

import { getBackendBaseUrl } from '../../utils/backendUrl';

function SourceCard({ source }) {
  return (
    <div className="rounded-lg border border-sidebar-border bg-background/40 p-4">
      <div className="text-sm font-semibold text-foreground">{source.path}</div>
      <div className="mt-3 space-y-2">
        {source.snippets.map((snippet, index) => (
          <p key={`${source.path}-${index}`} className="text-xs leading-6 text-muted-foreground">
            {snippet}
          </p>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ entry }) {
  const isUser = entry.role === 'user';
  return (
    <div className={`rounded-xl border p-4 ${isUser ? 'border-primary/30 bg-primary/10' : 'border-sidebar-border bg-card/70'}`}>
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {isUser ? 'You' : 'AiRA'}
      </div>
      <div className="whitespace-pre-wrap text-sm leading-7 text-foreground">{entry.content}</div>
    </div>
  );
}

function AiRAPage() {
  const apiBaseUrl = useMemo(() => getBackendBaseUrl(), []);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'AiRA is ready. Ask about the firmware, timing parameters, controller states, or the local project documentation.',
    },
  ]);
  const [sources, setSources] = useState([]);
  const [contextFiles, setContextFiles] = useState([]);
  const [status, setStatus] = useState({ type: 'info', text: 'Loading AiRA context…' });
  const [busy, setBusy] = useState(false);

  const quickPrompts = [
    'What does HOTWIRE_US control in the current workflow?',
    'Compare M_Duino_v001 and M_Duino_v002 at a high level.',
    'What are the main controller states mentioned in the docs?',
    'How do spark timing and DAQ timing relate in the current design?',
  ];

  const loadContext = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/aira/context`);
      const data = await response.json();
      if (!data.ok) throw new Error(data.message || 'Unable to load AiRA context.');
      setContextFiles(data.files || []);
      setStatus({ type: 'success', text: 'AiRA context loaded from documentation and firmware files.' });
    } catch (error) {
      setStatus({ type: 'error', text: error.message });
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadContext();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadContext]);

  const askQuestion = useCallback(async (nextQuestion) => {
    const trimmed = nextQuestion.trim();
    if (!trimmed) return;

    setBusy(true);
    setMessages((current) => [...current, { role: 'user', content: trimmed }]);
    setQuestion('');

    try {
      const response = await fetch(`${apiBaseUrl}/api/aira/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed }),
      });
      const data = await response.json();
      if (!data.ok) throw new Error(data.message || 'AiRA could not answer that question.');

      setMessages((current) => [...current, { role: 'assistant', content: data.answer }]);
      setSources(data.sources || []);
      setStatus({ type: 'success', text: 'AiRA returned grounded notes from the local repository context.' });
    } catch (error) {
      setMessages((current) => [...current, { role: 'assistant', content: `I hit a problem answering that: ${error.message}` }]);
      setStatus({ type: 'error', text: error.message });
    } finally {
      setBusy(false);
    }
  }, [apiBaseUrl]);

  return (
    <div className="space-y-6">
      <div className={`rounded-lg border px-4 py-3 text-sm ${status.type === 'error' ? 'border-red-500/40 bg-red-500/10 text-red-200' : 'border-border bg-card text-foreground'}`}>
        {status.text}
      </div>

      <section className="rounded-xl border border-sidebar-border bg-card p-6 lg:p-8">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_380px]">
          <div className="space-y-6">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">AiRA</div>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground">AI research assistant for firmware and controller context</h2>
              <p className="mt-4 text-sm leading-7 text-muted-foreground">
                Ask questions about the local documentation, firmware scripts, controller behavior, and parameter meanings.
                This first version is grounded in repository context rather than a remote model service.
              </p>
            </div>

            <div className="rounded-xl border border-sidebar-border bg-background/40 p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <BrainCircuit size={16} />
                  Conversation
                </div>
                <button
                  onClick={loadContext}
                  disabled={busy}
                  className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-xs font-semibold text-foreground hover:border-ring disabled:opacity-60"
                >
                  <RefreshCw size={14} />
                  Reload Context
                </button>
              </div>

              <div className="space-y-3">
                {messages.map((entry, index) => (
                  <MessageBubble key={`${entry.role}-${index}`} entry={entry} />
                ))}
              </div>

              <div className="mt-5 rounded-xl border border-sidebar-border bg-card p-4">
                <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-muted-foreground">Ask AiRA</label>
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="h-28 w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none"
                  placeholder="Ask about controller states, firmware versions, timing parameters, or project documentation..."
                />
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => askQuestion(question)}
                    disabled={busy || !question.trim()}
                    className="inline-flex items-center gap-2 rounded-md border border-primary/40 bg-primary/15 px-4 py-2 text-sm font-semibold text-primary disabled:opacity-60"
                  >
                    <Send size={14} />
                    Ask AiRA
                  </button>
                  <div className="inline-flex items-center gap-2 text-xs text-muted-foreground">
                    <ShieldAlert size={13} />
                    Grounded in local docs and firmware only
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <section className="rounded-xl border border-sidebar-border bg-background/40 p-5">
              <div className="text-sm font-semibold text-foreground">Quick prompts</div>
              <div className="mt-4 space-y-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => askQuestion(prompt)}
                    disabled={busy}
                    className="w-full rounded-lg border border-sidebar-border bg-card px-4 py-3 text-left text-sm text-foreground transition hover:border-primary/40 disabled:opacity-60"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </section>

            <section className="rounded-xl border border-sidebar-border bg-background/40 p-5">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <FileText size={16} />
                Context files
              </div>
              <div className="mt-4 space-y-2 max-h-64 overflow-y-auto pr-1">
                {contextFiles.map((file) => (
                  <div key={file} className="rounded-lg border border-sidebar-border bg-card px-3 py-2 text-xs text-muted-foreground">
                    {file}
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-xl border border-sidebar-border bg-background/40 p-5">
              <div className="text-sm font-semibold text-foreground">Sources used in the latest answer</div>
              <div className="mt-4 space-y-3">
                {sources.length ? (
                  sources.map((source) => <SourceCard key={source.path} source={source} />)
                ) : (
                  <div className="rounded-lg border border-sidebar-border bg-card px-4 py-3 text-xs text-muted-foreground">
                    Ask a question to see the matched documentation and firmware snippets here.
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AiRAPage;
