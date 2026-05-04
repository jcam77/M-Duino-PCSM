import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Code2, FileCode2, FolderTree, RefreshCw } from 'lucide-react';

import { getBackendBaseUrl } from '../../utils/backendUrl';

const CPP_KEYWORDS = new Set([
  'if', 'else', 'switch', 'case', 'default', 'for', 'while', 'do', 'break', 'continue', 'return',
  'void', 'bool', 'char', 'short', 'int', 'long', 'float', 'double', 'signed', 'unsigned',
  'const', 'static', 'volatile', 'struct', 'enum', 'class', 'typedef', 'namespace', 'using',
  'public', 'private', 'protected', 'template', 'typename', 'sizeof', 'true', 'false', 'nullptr',
]);

const ARDUINO_KEYWORDS = new Set([
  'HIGH', 'LOW', 'INPUT', 'OUTPUT', 'INPUT_PULLUP', 'pinMode', 'digitalWrite', 'digitalRead',
  'analogRead', 'analogWrite', 'delay', 'delayMicroseconds', 'micros', 'millis', 'Serial',
]);

const TYPE_KEYWORDS = new Set([
  'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t', 'int8_t', 'int16_t', 'int32_t', 'int64_t',
  'size_t', 'String',
]);

function createPalette(isLightTheme) {
  return isLightTheme
    ? {
        plain: '#1f2937',
        comment: '#3f6f4f',
        string: '#b45309',
        number: '#1d4ed8',
        keyword: '#7c3aed',
        type: '#0f766e',
        macro: '#be185d',
        accent: '#334155',
        lineNumber: '#64748b',
      }
    : {
        plain: '#e5e7eb',
        comment: '#7dd3a7',
        string: '#fbbf24',
        number: '#93c5fd',
        keyword: '#c4b5fd',
        type: '#5eead4',
        macro: '#f9a8d4',
        accent: '#cbd5e1',
        lineNumber: '#6b7280',
      };
}

function pushToken(tokens, text, type = 'plain') {
  if (!text) return;
  tokens.push({ text, type });
}

function classifyWord(word) {
  if (CPP_KEYWORDS.has(word) || ARDUINO_KEYWORDS.has(word)) return 'keyword';
  if (TYPE_KEYWORDS.has(word)) return 'type';
  if (/^[A-Z_][A-Z0-9_]*$/.test(word)) return 'macro';
  return 'plain';
}

function highlightCpp(source) {
  const lines = (source || '').split('\n');
  const highlighted = [];
  let inBlockComment = false;

  for (const line of lines) {
    const tokens = [];
    let index = 0;

    if (!inBlockComment && line.trimStart().startsWith('#')) {
      highlighted.push([{ text: line, type: 'macro' }]);
      continue;
    }

    while (index < line.length) {
      const slice = line.slice(index);

      if (inBlockComment) {
        const end = slice.indexOf('*/');
        if (end === -1) {
          pushToken(tokens, slice, 'comment');
          index = line.length;
          break;
        }
        pushToken(tokens, slice.slice(0, end + 2), 'comment');
        index += end + 2;
        inBlockComment = false;
        continue;
      }

      if (slice.startsWith('//')) {
        pushToken(tokens, slice, 'comment');
        index = line.length;
        break;
      }

      if (slice.startsWith('/*')) {
        const end = slice.indexOf('*/', 2);
        if (end === -1) {
          pushToken(tokens, slice, 'comment');
          inBlockComment = true;
          index = line.length;
          break;
        }
        pushToken(tokens, slice.slice(0, end + 2), 'comment');
        index += end + 2;
        continue;
      }

      const char = line[index];

      if (char === '"' || char === '\'') {
        const quote = char;
        let end = index + 1;
        let escaped = false;
        while (end < line.length) {
          const nextChar = line[end];
          if (escaped) {
            escaped = false;
          } else if (nextChar === '\\') {
            escaped = true;
          } else if (nextChar === quote) {
            end += 1;
            break;
          }
          end += 1;
        }
        pushToken(tokens, line.slice(index, end), 'string');
        index = end;
        continue;
      }

      if (/\d/.test(char)) {
        let end = index + 1;
        while (end < line.length && /[\dA-Fa-fxX._]/.test(line[end])) end += 1;
        pushToken(tokens, line.slice(index, end), 'number');
        index = end;
        continue;
      }

      if (/[A-Za-z_]/.test(char)) {
        let end = index + 1;
        while (end < line.length && /[A-Za-z0-9_]/.test(line[end])) end += 1;
        const word = line.slice(index, end);
        pushToken(tokens, word, classifyWord(word));
        index = end;
        continue;
      }

      if (/\s/.test(char)) {
        let end = index + 1;
        while (end < line.length && /\s/.test(line[end])) end += 1;
        pushToken(tokens, line.slice(index, end), 'plain');
        index = end;
        continue;
      }

      pushToken(tokens, char, 'accent');
      index += 1;
    }

    highlighted.push(tokens.length ? tokens : [{ text: '', type: 'plain' }]);
  }

  return highlighted;
}

function FirmwarePage() {
  const apiBaseUrl = useMemo(() => getBackendBaseUrl(), []);
  const [scripts, setScripts] = useState([]);
  const [selectedScript, setSelectedScript] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState({ type: 'info', text: 'Loading firmware scripts…' });
  const [busy, setBusy] = useState(false);
  const [isLightTheme, setIsLightTheme] = useState(() => (
    typeof document !== 'undefined' && document.documentElement.classList.contains('light')
  ));

  useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    const root = document.documentElement;
    const syncTheme = () => setIsLightTheme(root.classList.contains('light'));
    syncTheme();
    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  const palette = useMemo(() => createPalette(isLightTheme), [isLightTheme]);
  const highlightedLines = useMemo(() => highlightCpp(content), [content]);

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
            <div className="mb-3 text-[11px] text-muted-foreground">
              Comments, strings, numeric values, macros, and control keywords are highlighted to make firmware review easier.
            </div>
            <div className="min-h-[520px] overflow-x-auto rounded-lg border border-sidebar-border bg-background p-0 text-xs leading-6">
              {!content ? (
                <div className="p-4 text-foreground">Select a firmware script to view its contents.</div>
              ) : (
                <pre className="m-0 min-h-[520px] bg-transparent p-4" style={{ color: palette.plain }}>
                  <code>
                    {highlightedLines.map((lineTokens, lineIndex) => (
                      <div key={`${selectedScript}-${lineIndex}`} className="flex">
                        <span
                          className="shrink-0 select-none pr-4 text-right"
                          style={{ width: '3.75rem', color: palette.lineNumber }}
                        >
                          {lineIndex + 1}
                        </span>
                        <span className="flex-1 whitespace-pre-wrap break-words">
                          {lineTokens.map((token, tokenIndex) => (
                            <span
                              key={`${selectedScript}-${lineIndex}-${tokenIndex}`}
                              style={{
                                color: palette[token.type] || palette.plain,
                                fontStyle: token.type === 'comment' ? 'italic' : 'normal',
                                fontWeight: token.type === 'keyword' || token.type === 'type' ? 600 : 400,
                              }}
                            >
                              {token.text}
                            </span>
                          ))}
                        </span>
                      </div>
                    ))}
                  </code>
                </pre>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default FirmwarePage;
