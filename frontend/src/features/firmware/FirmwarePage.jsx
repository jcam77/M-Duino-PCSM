import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Code2, FileCode2, FolderTree, RefreshCw } from 'lucide-react';

import { getBackendBaseUrl } from '../../utils/backendUrl';

function FirmwarePage() {
  const apiBaseUrl = useMemo(() => getBackendBaseUrl(), []);
  const [scripts, setScripts] = useState([]);
  const [selectedScript, setSelectedScript] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState({ type: 'info', text: 'Loading firmware scripts…' });
  const [busy, setBusy] = useState(false);

  const loadContent = useCallback(async (scriptPath) => {
    if (!scriptPath) {
      setContent('');
      return;
    }
    try {
      const response = await fetch(`${apiBaseUrl}/api/firmware/script?path=${encodeURIComponent(scriptPath)}`);
      const data = await response.json();
      if (!data.ok) throw new Error(data.message || 'Unable to load firmware script content.');
      setContent(data.content || '');
      setSelectedScript(data.path || scriptPath);
    } catch (error) {
      setStatus({ type: 'error', text: error.message });
    }
  }, [apiBaseUrl]);

  const loadScripts = useCallback(async (preferredPath = '') => {
    setBusy(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/firmware/scripts`);
      const data = await response.json();
      if (!data.ok) throw new Error(data.message || 'Unable to load firmware scripts.');
      const files = data.scripts || [];
      setScripts(files);
      const nextPath = preferredPath || selectedScript || files[0]?.path || '';
      setSelectedScript(nextPath);
      setStatus({ type: 'success', text: files.length ? 'Firmware scripts loaded.' : 'No firmware scripts found.' });
      if (nextPath) {
        await loadContent(nextPath);
      } else {
        setContent('');
      }
    } catch (error) {
      setStatus({ type: 'error', text: error.message });
    } finally {
      setBusy(false);
    }
  }, [apiBaseUrl, loadContent, selectedScript]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadScripts();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadScripts]);

  return (
    <div className="space-y-6">
      <div className={`rounded-lg border px-4 py-3 text-sm ${status.type === 'error' ? 'border-red-500/40 bg-red-500/10 text-red-200' : 'border-border bg-card text-foreground'}`}>
        {status.text}
      </div>

      <section className="rounded-xl border border-sidebar-border bg-card p-6 lg:p-8">
        <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
          <div className="space-y-6">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">Firmware</div>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground">M-Duino firmware scripts</h2>
              <p className="mt-4 text-sm leading-7 text-muted-foreground">
                Review the `.ino` files stored in `M-DuinoScripts` directly from the app. This page is for reference while checking the
                controller logic, comparing revisions, and aligning the UI with the active firmware contract.
              </p>
            </div>

            <div className="rounded-xl border border-sidebar-border bg-background/40 p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <FolderTree size={16} />
                  Script Files
                </div>
                <button
                  onClick={() => loadScripts(selectedScript)}
                  disabled={busy}
                  className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-xs font-semibold text-foreground hover:border-ring disabled:opacity-60"
                >
                  <RefreshCw size={14} />
                  Reload
                </button>
              </div>

              <div className="space-y-2">
                {scripts.map((script) => (
                  <button
                    key={script.path}
                    onClick={() => loadContent(script.path)}
                    className={`w-full rounded-lg border px-4 py-3 text-left transition ${
                      selectedScript === script.path
                        ? 'border-primary/40 bg-primary/10 text-primary'
                        : 'border-sidebar-border bg-card text-foreground hover:border-ring'
                    }`}
                  >
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <FileCode2 size={15} />
                      {script.name}
                    </div>
                    <div className="mt-1 text-[11px] text-muted-foreground">{script.path}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-sidebar-border bg-background/40 p-5">
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
              <Code2 size={16} />
              {selectedScript || 'Script Preview'}
            </div>
            <pre className="min-h-[520px] overflow-x-auto rounded-lg border border-sidebar-border bg-background p-4 text-xs leading-6 text-foreground">
              <code>{content || 'Select a firmware script to view its contents.'}</code>
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
}

export default FirmwarePage;
