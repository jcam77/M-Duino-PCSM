import React, { useEffect, useState } from 'react';
import { BrainCircuit, Cable, Code2, Home, Moon, RefreshCw, Sun } from 'lucide-react';

import AiRAPage from '../features/aira/AiRAPage';
import FirmwarePage from '../features/firmware/FirmwarePage';
import HomePage from '../features/home/HomePage';
import WorkspacePage from '../features/workspace/WorkspacePage';
import { getPublicUrl } from '../utils/assetUrl';

/* global __APP_VERSION__, __LAST_UPDATED__ */

function AppShell() {
  const [isLight, setIsLight] = useState(() => {
    if (typeof window === 'undefined') return false;
    const stored = window.localStorage.getItem('mduino-theme');
    if (stored === 'light') return true;
    if (stored === 'dark') return false;
    return window.matchMedia?.('(prefers-color-scheme: light)')?.matches ?? false;
  });
  const [activePage, setActivePage] = useState('home');

  useEffect(() => {
    document.documentElement.classList.toggle('light', isLight);
    window.localStorage.setItem('mduino-theme', isLight ? 'light' : 'dark');
  }, [isLight]);

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
    <div className="w-full min-h-screen bg-background text-foreground flex flex-col overflow-hidden">
      <header className="w-full sticky top-0 z-50 border-b border-sidebar-border/60 bg-background/80 backdrop-blur">
        <div className="w-full min-h-[96px] px-4 pt-3 pb-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <a
                href="https://www.lunduniversity.lu.se/lucat/group/v1000219"
                target="_blank"
                rel="noreferrer"
                aria-label="Open Lund University group page"
                className="inline-flex items-center"
              >
                <img src={getPublicUrl(isLight ? 'university_logo-LightMode.png' : 'university_logo-DarkMode.png')} alt="University" className="h-10 object-contain" />
              </a>
              <div className="h-8 w-px bg-sidebar-border mx-1 hidden md:block"></div>
              <a
                href="https://brandogsikring.dk/en/research-and-development/energy-and-transport/validation-in-depth-analysis-and-development-of-available-explosion-models-for-p2x-applications/"
                target="_blank"
                rel="noreferrer"
                aria-label="Open institute project page"
                className="inline-flex items-center"
              >
                <img src={getPublicUrl(isLight ? 'institute_logo-LightMode.png' : 'institute_logo-DarkMode.png')} alt="Institute" className="h-10 object-contain" />
              </a>
              <div className="ml-4">
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                    <Cable size={18} />
                    M-Duino PCSM
                  </h1>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Controller setup, live monitoring, parameter input, firmware reference, and event review.
                </p>
                <p className="mt-2 text-[10px] text-muted-foreground uppercase tracking-[0.2em]">
                  Single-workspace controller application
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActivePage('home')}
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-md border text-xs font-semibold transition ${
                    activePage === 'home'
                      ? 'border-primary bg-primary/15 text-primary'
                      : 'border-border text-foreground hover:border-ring'
                  }`}
                  title="Home"
                  aria-label="Home"
                >
                  <Home size={16} />
                </button>
                <button
                  onClick={() => setActivePage('workspace')}
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-md border text-xs font-semibold transition ${
                    activePage === 'workspace'
                      ? 'border-primary bg-primary/15 text-primary'
                      : 'border-border text-foreground hover:border-ring'
                  }`}
                  title="Controller Workspace"
                  aria-label="Controller Workspace"
                >
                  <Cable size={16} />
                </button>
                <button
                  onClick={() => setActivePage('aira')}
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-md border text-xs font-semibold transition ${
                    activePage === 'aira'
                      ? 'border-primary bg-primary/15 text-primary'
                      : 'border-border text-foreground hover:border-ring'
                  }`}
                  title="AiRA"
                  aria-label="AiRA"
                >
                  <BrainCircuit size={16} />
                </button>
                <button
                  onClick={() => setActivePage('firmware')}
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-md border text-xs font-semibold transition ${
                    activePage === 'firmware'
                      ? 'border-primary bg-primary/15 text-primary'
                      : 'border-border text-foreground hover:border-ring'
                  }`}
                  title="Firmware Scripts"
                  aria-label="Firmware Scripts"
                >
                  <Code2 size={16} />
                </button>
              </div>
              <button
                onClick={() => setIsLight((value) => !value)}
                className="inline-flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground transition"
                aria-pressed={isLight}
                role="switch"
                aria-checked={isLight}
                title={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
              >
                <span className={`relative inline-flex h-5 w-9 items-center rounded-full border border-sidebar-border transition ${isLight ? 'bg-primary/25' : 'bg-muted/60'}`}>
                  <span className={`inline-flex h-3.5 w-3.5 transform items-center justify-center rounded-full bg-foreground text-background transition ${isLight ? 'translate-x-4' : 'translate-x-1'}`}>
                    {isLight ? <Sun size={10} /> : <Moon size={10} />}
                  </span>
                </span>
              </button>
              <button
                onClick={() => window.location.reload()}
                className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-border text-xs font-semibold text-foreground hover:border-ring"
                title="Reload app"
                aria-label="Reload app"
              >
                <RefreshCw size={16} />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full p-6 flex-1 overflow-y-auto scroll-smooth">
        {activePage === 'home' ? (
          <HomePage
            onOpenWorkspace={() => setActivePage('workspace')}
            onOpenFirmware={() => setActivePage('firmware')}
            onOpenAiRA={() => setActivePage('aira')}
          />
        ) : activePage === 'aira' ? (
          <AiRAPage />
        ) : activePage === 'firmware' ? (
          <FirmwarePage />
        ) : (
          <WorkspacePage />
        )}
      </main>

      <footer className="px-4 sm:px-6 lg:px-8 pb-6">
        <div className="max-w-6xl mx-auto mt-1 flex flex-col md:flex-row md:items-center md:justify-between border-t border-sidebar-border/60 pt-4 text-[10px] text-muted-foreground">
          <span>© 2026 M-Duino-PCSM. Controller supervision workspace.</span>
          <span>Built for trigger-box monitoring, parameter control, firmware review, and AiRA research support.</span>
          <span className="inline-block text-xs text-muted-foreground bg-card/70 rounded px-2 py-0.5 mt-1 md:mt-0 md:ml-4">
            M-Duino-PCSM {displayVersion} &nbsp;|&nbsp; Last updated: {lastUpdatedLabel}
          </span>
        </div>
      </footer>
    </div>
  );
}

export default AppShell;
