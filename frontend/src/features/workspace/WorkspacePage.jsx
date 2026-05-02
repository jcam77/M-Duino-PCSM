import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  Cable,
  FolderOpen,
  RefreshCw,
  SlidersHorizontal,
  TerminalSquare,
  Zap,
} from 'lucide-react';

import { getBackendBaseUrl } from '../../utils/backendUrl';

const snapshotToParameterValues = (snapshot, parameterDefinitions) => {
  const next = {};
  parameterDefinitions.forEach((definition) => {
    next[definition.protocol_name] = snapshot?.parameters?.[definition.protocol_name] ?? definition.default;
  });
  return next;
};

const StatusMetric = ({ label, value, mono = false }) => (
  <div className="rounded-lg border border-sidebar-border bg-card p-4">
    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
    <div className={`mt-2 text-sm font-semibold text-foreground ${mono ? 'font-mono' : ''}`}>{value}</div>
  </div>
);

const StatusSignal = ({ label, active }) => (
  <div className={`rounded-lg border p-4 ${active ? 'border-primary/35 bg-primary/10' : 'border-sidebar-border bg-card'}`}>
    <div className="flex items-center gap-3">
      <span className={`h-2.5 w-2.5 rounded-full ${active ? 'bg-primary' : 'bg-muted-foreground/50'}`}></span>
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
        <div className="mt-1 text-sm font-semibold text-foreground">{active ? 'High' : 'Low'}</div>
      </div>
    </div>
  </div>
);

function WorkspacePage() {
  const apiBaseUrl = useMemo(() => getBackendBaseUrl(), []);
  const [availableBackends, setAvailableBackends] = useState([]);
  const [backend, setBackend] = useState('Mock controller');
  const [ports, setPorts] = useState([]);
  const [selectedPort, setSelectedPort] = useState('');
  const [snapshot, setSnapshot] = useState(null);
  const [parameterDefinitions, setParameterDefinitions] = useState([]);
  const [parameterValues, setParameterValues] = useState({});
  const [message, setMessage] = useState({ type: 'success', text: 'Loading workspace…' });
  const [busy, setBusy] = useState(false);

  const loadBootstrap = useCallback(async (targetBackend = backend, preserveValues = false) => {
    const response = await fetch(`${apiBaseUrl}/api/controller/bootstrap?backend=${encodeURIComponent(targetBackend)}`);
    const data = await response.json();
    if (!data.ok) throw new Error(data.message || 'Unable to load controller bootstrap.');
    setAvailableBackends(data.backends || []);
    setBackend(data.backend);
    setPorts(data.ports || []);
    setSelectedPort((current) => current || data.ports?.[0] || '');
    setSnapshot(data.snapshot);
    setParameterDefinitions(data.parameterDefinitions || []);
    if (!preserveValues) {
      setParameterValues(snapshotToParameterValues(data.snapshot, data.parameterDefinitions || []));
    }
    return data;
  }, [apiBaseUrl, backend]);

  const loadSnapshot = useCallback(async (targetBackend = backend) => {
    const response = await fetch(`${apiBaseUrl}/api/controller/snapshot?backend=${encodeURIComponent(targetBackend)}`);
    const data = await response.json();
    if (!data.ok) throw new Error(data.message || 'Unable to refresh controller snapshot.');
    setPorts(data.ports || []);
    setSnapshot(data.snapshot);
  }, [apiBaseUrl, backend]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadBootstrap().then(() => {
        setMessage({ type: 'success', text: 'Workspace ready.' });
      }).catch((error) => {
        setMessage({ type: 'error', text: error.message });
      });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadBootstrap]);

  useEffect(() => {
    if (!backend) return;
    const timer = window.setInterval(() => {
      loadSnapshot(backend).catch(() => {});
    }, 1500);
    return () => window.clearInterval(timer);
  }, [backend, loadSnapshot]);

  const syncAction = async (path, body, options = {}) => {
    setBusy(true);
    try {
      const response = await fetch(`${apiBaseUrl}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      setSnapshot(data.snapshot);
      setPorts(data.ports || []);
      if (data.parameterDefinitions) setParameterDefinitions(data.parameterDefinitions);
      if (!options.preserveValues && data.snapshot) {
        setParameterValues(snapshotToParameterValues(data.snapshot, data.parameterDefinitions || parameterDefinitions));
      }
      setMessage({ type: data.ok ? 'success' : 'error', text: data.message || 'Action completed.' });
      return data;
    } finally {
      setBusy(false);
    }
  };

  const status = snapshot?.status;
  const events = snapshot?.events || [];

  return (
    <div>
      <div className={`mb-6 rounded-lg border px-4 py-3 text-sm ${message.type === 'error' ? 'border-red-500/40 bg-red-500/10 text-red-200' : 'border-border bg-card text-foreground'}`}>
        {message.text}
      </div>

      <div className="mb-5 rounded-lg border border-sidebar-border bg-card px-4 py-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">Controller Workspace</div>
            <div className="mt-1 text-sm text-muted-foreground">
              Active backend: <span className="font-semibold text-foreground">{backend}</span>
            </div>
          </div>
          <button
            onClick={() => loadBootstrap(backend, true).then(() => setMessage({ type: 'success', text: 'Workspace refreshed.' })).catch((error) => setMessage({ type: 'error', text: error.message }))}
            className="inline-flex items-center justify-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-semibold text-foreground hover:border-ring"
            title="Refresh workspace"
            aria-label="Refresh workspace"
          >
            <RefreshCw size={15} />
            Refresh Workspace
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <div className="space-y-6">
          <section className="rounded-xl border border-sidebar-border bg-card p-6">
            <div className="mb-4">
              <div className="text-xl font-bold tracking-tight">Connection</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Choose the active backend, inspect detected ports, then connect to begin live monitoring.
              </div>
            </div>

            <div className="mb-5 rounded-lg border border-primary/30 bg-primary/10 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">User Input Area</div>
              <div className="mt-2 text-sm text-foreground">
                Timing and control parameters are entered in the <span className="font-semibold">User Input Parameters</span> panel on the right.
              </div>
              <a
                href="#user-input-parameters"
                className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:opacity-80"
              >
                Go to parameter inputs
                <ArrowRight size={14} />
              </a>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-muted-foreground">Backend</label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground"
                  value={backend}
                  onChange={(event) => {
                    const nextBackend = event.target.value;
                    setBackend(nextBackend);
                    loadBootstrap(nextBackend).catch((error) => setMessage({ type: 'error', text: error.message }));
                  }}
                >
                  {availableBackends.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-muted-foreground">Port</label>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground"
                  value={selectedPort}
                  onChange={(event) => setSelectedPort(event.target.value)}
                >
                  {(ports.length ? ports : ['No ports found']).map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <button
                  disabled={busy}
                  onClick={() => loadBootstrap(backend, true).then((data) => setSelectedPort((current) => current || data.ports?.[0] || '')).catch((error) => setMessage({ type: 'error', text: error.message }))}
                  className="inline-flex items-center justify-center rounded-md border border-border px-3 py-2 text-sm font-semibold text-foreground hover:border-ring disabled:opacity-60"
                >
                  <FolderOpen size={15} className="mr-2" />
                  Ports
                </button>
                <button
                  disabled={busy}
                  onClick={() => syncAction('/api/controller/connect', { backend, port: selectedPort })}
                  className="inline-flex items-center justify-center rounded-md border border-primary/40 bg-primary/15 px-3 py-2 text-sm font-semibold text-primary disabled:opacity-60"
                >
                  <Cable size={15} className="mr-2" />
                  Connect
                </button>
                <button
                  disabled={busy}
                  onClick={() => syncAction('/api/controller/disconnect', { backend })}
                  className="inline-flex items-center justify-center rounded-md border border-border px-3 py-2 text-sm font-semibold text-foreground disabled:opacity-60"
                >
                  Disconnect
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  disabled={busy}
                  onClick={() => loadSnapshot(backend).then(() => setMessage({ type: 'success', text: 'Status refreshed.' })).catch((error) => setMessage({ type: 'error', text: error.message }))}
                  className="inline-flex items-center justify-center rounded-md border border-border px-3 py-2 text-sm font-semibold text-foreground disabled:opacity-60"
                >
                  <RefreshCw size={15} className="mr-2" />
                  Reload
                </button>
                <button
                  disabled={busy}
                  onClick={() => syncAction('/api/controller/demo', { backend })}
                  className="inline-flex items-center justify-center rounded-md border border-border px-3 py-2 text-sm font-semibold text-foreground disabled:opacity-60"
                >
                  <Zap size={15} className="mr-2" />
                  Demo
                </button>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-sidebar-border bg-card p-6">
            <div className="mb-4">
              <div className="text-xl font-bold tracking-tight">Live Status</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Controller state, inputs, timing flags, and last-known reason from the firmware.
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <StatusSignal label="Arm Input" active={Boolean(status?.arm_input)} />
              <StatusSignal label="Trigger Input" active={Boolean(status?.trigger_input)} />
              <StatusSignal label="Spark Active" active={Boolean(status?.spark_active)} />
              <StatusSignal label="DAQ Active" active={Boolean(status?.daq_active)} />
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <StatusMetric label="Controller State" value={status?.controller_state || '--'} />
              <StatusMetric label="Mode" value={status?.mode || '--'} />
              <StatusMetric label="Connection" value={status?.connection_status || '--'} />
              <StatusMetric label="Last Reason" value={status?.last_reason || '--'} />
              <StatusMetric label="Firmware" value={status?.firmware_version || '--'} mono />
              <StatusMetric label="Last State Change" value={status?.last_state_change || '--'} mono />
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section id="user-input-parameters" className="rounded-xl border border-sidebar-border bg-card p-6 scroll-mt-28">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">Operator Input</div>
                <div className="mt-2 text-xl font-bold tracking-tight">User Input Parameters</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  Enter or adjust the controller timing values here, then apply them to the active backend.
                </div>
              </div>
              <div className="inline-flex items-center gap-2 rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-semibold uppercase tracking-widest text-primary">
                <SlidersHorizontal size={14} />
                Editable
              </div>
            </div>

            <div className="mb-5 rounded-lg border border-sidebar-border bg-background/40 px-4 py-3 text-sm text-muted-foreground">
              These fields are the direct user inputs for dwell times, delays, and trigger-related settings.
            </div>

            <div className="grid gap-5 2xl:grid-cols-2">
              {parameterDefinitions.map((definition) => (
                <div key={definition.protocol_name} className="rounded-lg border border-sidebar-border bg-background/40 p-4">
                  <div className="text-sm font-semibold text-foreground">{definition.label}</div>
                  <div className="mt-1 text-[11px] text-muted-foreground">
                    <span className="font-mono">{definition.protocol_name}</span>
                    {definition.ui_unit ? ` · ${definition.ui_unit}` : ''}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">{definition.help_text}</div>
                  <div className="mt-3">
                    {definition.kind === 'bool' ? (
                      <label className="inline-flex items-center gap-3 text-sm text-foreground">
                        <input
                          type="checkbox"
                          checked={Boolean(parameterValues[definition.protocol_name])}
                          onChange={(event) => setParameterValues((current) => ({ ...current, [definition.protocol_name]: event.target.checked }))}
                        />
                        Enabled
                      </label>
                    ) : (
                      <div className="flex items-center gap-3">
                        <input
                          type="number"
                          step={definition.step}
                          value={parameterValues[definition.protocol_name] ?? ''}
                          onChange={(event) => setParameterValues((current) => ({
                            ...current,
                            [definition.protocol_name]: definition.kind === 'int' ? Number(event.target.value) : event.target.value === '' ? '' : Number(event.target.value),
                          }))}
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground"
                        />
                        {definition.ui_unit ? (
                          <span className="min-w-12 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                            {definition.ui_unit}
                          </span>
                        ) : null}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5">
              <button
                disabled={busy}
                onClick={() => syncAction('/api/controller/parameters', { backend, values: parameterValues })}
                className="inline-flex items-center rounded-md border border-primary/40 bg-primary/15 px-4 py-2 text-sm font-semibold text-primary disabled:opacity-60"
              >
                Apply Parameter Changes
              </button>
            </div>
          </section>

          <section className="rounded-xl border border-sidebar-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <div className="text-xl font-bold tracking-tight">Event Log</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  Transition lines, startup configuration, acknowledgements, and serial monitoring output.
                </div>
              </div>
              <TerminalSquare className="text-muted-foreground" size={18} />
            </div>

            <div className="rounded-lg border border-sidebar-border bg-background/40 p-4">
              <textarea
                readOnly
                className="h-[360px] w-full resize-none border-0 bg-transparent text-sm text-foreground outline-none"
                value={events.map((event) => `[${new Date(event.timestamp).toLocaleTimeString()}] ${event.message}`).join('\n')}
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default WorkspacePage;
