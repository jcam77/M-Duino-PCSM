import React from 'react';
import {
  ArrowRight,
  Cable,
  Clock3,
  Code2,
  Cpu,
  Radio,
  ShieldAlert,
  SlidersHorizontal,
  TerminalSquare,
} from 'lucide-react';

/* global __APP_VERSION__, __LAST_UPDATED__ */

function MetricTile({ value, label }) {
  return (
    <div className="p-4 rounded-lg border border-sidebar-border/30 bg-card/50">
      <p className="text-2xl font-bold text-primary">{value}</p>
      <p className="text-muted-foreground text-xs mt-1">{label}</p>
    </div>
  );
}

function FeatureCard({ icon, title, children }) {
  const IconComponent = icon;
  return (
    <section className="rounded-xl border border-sidebar-border bg-card p-8 hover:border-primary/50 transition">
      <div className="w-12 h-12 rounded-md border border-primary/30 bg-primary/10 flex items-center justify-center mb-4">
        <IconComponent className="text-primary" size={22} />
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-muted-foreground text-sm leading-6">{children}</p>
    </section>
  );
}

function HomePage({ onOpenWorkspace, onOpenFirmware, onOpenAiRA }) {
  const formatDate = (value) => {
    if (!value) return 'Unknown';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(date);
  };

  const appVersion = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.1.0';
  const displayVersion = appVersion.replace(/\.0$/, '');
  const hasUncommittedChanges = /-dirty$/.test(displayVersion);
  const lastUpdatedRaw = typeof __LAST_UPDATED__ !== 'undefined' ? __LAST_UPDATED__ : '';
  const effectiveLastUpdated = hasUncommittedChanges ? new Date().toISOString() : lastUpdatedRaw;
  const lastUpdatedLabel = effectiveLastUpdated ? formatDate(effectiveLastUpdated) : 'Unknown';

  return (
    <div className="w-full h-full overflow-y-auto scroll-smooth snap-y snap-mandatory">
      <section className="relative min-h-[84vh] flex items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8 pt-4 pb-12 snap-start">
        <div className="absolute inset-0 z-0">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/5 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center">
          <h1 className="normal-case text-5xl sm:text-6xl lg:text-7xl font-bold mb-4 leading-tight">
            <span className="text-foreground">M-Duino Controller</span>
            <br />
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Management Platform
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground mb-6 max-w-3xl mx-auto">
            Operator-focused workspace for serial connection, live controller monitoring, parameter editing,
            firmware review, and event tracking around the M-Duino PCSM workflow.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-10">
            <button
              onClick={onOpenWorkspace}
              className="inline-flex items-center gap-2 rounded-md border border-primary/30 px-4 py-2 text-sm font-semibold text-foreground hover:border-primary/60 transition"
            >
              <Cable size={18} /> Open Controller Workspace
            </button>
            <button
              onClick={onOpenFirmware}
              className="inline-flex items-center gap-2 rounded-md border border-primary/30 px-4 py-2 text-sm font-semibold text-foreground hover:border-primary/60 transition"
            >
              <Code2 size={18} /> View Firmware Scripts
            </button>
            <button
              onClick={onOpenAiRA}
              className="inline-flex items-center gap-2 rounded-md border border-primary/30 px-4 py-2 text-sm font-semibold text-foreground hover:border-primary/60 transition"
            >
              <Cpu size={18} /> Open AiRA
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-16 text-sm">
            <MetricTile value="USB / Mock" label="Backend Modes" />
            <MetricTile value="Live" label="Status Monitoring" />
            <MetricTile value="Editable" label="Operator Parameters" />
            <MetricTile value="Versioned" label="Firmware Snapshots" />
          </div>
        </div>
      </section>

      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-card/20 snap-start">
        <div className="max-w-[90rem] mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              Core Capabilities For The Controller Workflow
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              A focused app for connecting to the controller, monitoring its live state, updating approved values,
              and checking the firmware context behind the current setup.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard icon={Cable} title="Connection Management">
              Switch between the mock backend and the USB serial backend, inspect detected ports, and manage live controller sessions.
            </FeatureCard>
            <FeatureCard icon={Radio} title="Live Signal Monitoring">
              Watch arm, trigger, spark, and DAQ states in one operator-facing workspace with status feedback from the backend.
            </FeatureCard>
            <FeatureCard icon={SlidersHorizontal} title="Parameter Input">
              Edit dwell times, delays, and related operator values through the user input panel, then apply them to the active backend.
            </FeatureCard>
            <FeatureCard icon={TerminalSquare} title="Event Log Review">
              Read transition lines, startup configuration, acknowledgements, and serial output in a single event log view.
            </FeatureCard>
            <FeatureCard icon={Code2} title="Firmware Reference">
              Open the `.ino` files stored in `M-DuinoScripts` directly in the app to compare revisions and align the UI with the embedded logic.
            </FeatureCard>
            <FeatureCard icon={Cpu} title="AiRA Research Assistant">
              Ask grounded questions about the local documentation and firmware files, then review the exact matched sources behind each response.
            </FeatureCard>
            <FeatureCard icon={ShieldAlert} title="Operator Awareness">
              Keep the workflow explicit and reviewable before applying changes that affect spark timing, DAQ timing, or trigger behavior.
            </FeatureCard>
          </div>
        </div>
      </section>

      <section className="py-20 px-4 sm:px-6 lg:px-8 snap-start">
        <div className="max-w-6xl mx-auto grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.9fr)]">
          <div className="rounded-xl border border-sidebar-border bg-card p-8">
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">Recommended Workflow</div>
            <h2 className="mt-3 text-3xl font-bold tracking-tight">Move from connection to verified controller setup with fewer blind steps</h2>
            <ol className="mt-6 space-y-4 text-sm leading-7 text-muted-foreground">
              <li>1. Open `Controller Workspace` and start with `Mock controller` if you want to confirm the UI flow first.</li>
              <li>2. Switch to `USB serial`, pick the correct device port, and connect to the hardware.</li>
              <li>3. Review the live status panel and event log to confirm the controller is reporting the expected state.</li>
              <li>4. Enter timing values in `User Input Parameters` and apply them to the active backend.</li>
              <li>5. Use `Firmware Scripts` when you need to cross-check the current embedded logic or compare firmware revisions.</li>
            </ol>
          </div>

          <div className="rounded-xl border border-primary/25 bg-primary/10 p-6">
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">Operator Note</div>
            <p className="mt-4 text-sm leading-7 text-foreground">
              This app supervises and documents the controller workflow, but the embedded firmware still owns the timing execution,
              sequence logic, and safety decisions. Review values carefully before applying them to live hardware.
            </p>
            <div className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
              <Clock3 size={14} />
              Backend defaults: `127.0.0.1:5001` and frontend defaults: `127.0.0.1:5174`
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
              <Cpu size={14} />
              Serial write support depends on the matching firmware command contract.
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 sm:px-6 lg:px-8 pb-8">
        <div className="max-w-6xl mx-auto mt-1 flex flex-col md:flex-row md:items-center md:justify-between border-t border-sidebar-border/60 pt-4 text-[10px] text-muted-foreground">
          <span>© 2026 M-Duino-PCSM. Controller supervision workspace.</span>
          <span>Built for trigger-box monitoring, parameter control, and firmware review.</span>
          <span className="inline-block text-xs text-muted-foreground bg-card/70 rounded px-2 py-0.5 mt-1 md:mt-0 md:ml-4">
            M-Duino-PCSM {displayVersion} &nbsp;|&nbsp; Last updated: {lastUpdatedLabel}
          </span>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
