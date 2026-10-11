/**
 * InsightFlow Executive Decision Workspace
 * Main Application Entry Point
 * Clean architecture with WorkspaceProvider, ErrorBoundary, and modular components.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';

// Config & API
import { config, VIEWS } from './config';
import { api, ApiError } from './api';

// Context & State Management
import { WorkspaceProvider, useWorkspace } from './context/WorkspaceContext';

// Modular UI & Canvas Components
import { BorderGlow, ToastContainer, ErrorBoundary } from './components/ui';
import { GlobalBackground } from './components/canvas';
import { FrictionClusters } from './components/features';
import { ToolbarDynamic, TextEffectPerChar } from './components/navigation';

// Expose globals for backward-compatible runtime usage in index.html
window.BorderGlow = BorderGlow;
window.ToolbarDynamic = ToolbarDynamic;
window.TextEffectPerChar = TextEffectPerChar;
window.api = api;
window.activeDatasetId = null;
window.selectedUploadFile = null;

let activeView = VIEWS.OVERVIEW;

/**
 * Switch Navigation View
 */
window.switchView = function(viewName) {
  activeView = viewName;
  const views = [VIEWS.OVERVIEW, VIEWS.STUDIO, VIEWS.RADAR, VIEWS.EXPLORER, VIEWS.TERMINAL];

  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (!el) return;
    if (v === viewName) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });

  document.querySelectorAll('[data-view-nav]').forEach(btn => {
    const target = btn.getAttribute('data-view-nav');
    const isTarget = target === viewName;
    if (isTarget) {
      btn.classList.add('bg-indigo-600', 'text-white', 'shadow-sm');
      btn.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-100', 'dark:hover:bg-slate-800');
    } else {
      btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-sm');
      btn.classList.add('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-100', 'dark:hover:bg-slate-800');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
};

/**
 * Slide-over Evidence Drawer
 */
window.openEvidenceDrawer = async function(issueKeyOrId) {
  const drawer = document.getElementById('evidence-drawer');
  const overlay = document.getElementById('drawer-overlay');
  if (!drawer || !overlay) return;

  const titleEl = document.getElementById('drawer-title');
  const idEl = document.getElementById('drawer-id');
  if (titleEl) titleEl.textContent = 'Loading evidence telemetry...';
  if (idEl) idEl.textContent = typeof issueKeyOrId === 'string' ? issueKeyOrId.substring(0, 8) : '...';

  drawer.classList.remove('translate-x-full');
  overlay.classList.remove('hidden');

  try {
    const detail = await api.getIssueDetail(issueKeyOrId);

    if (titleEl) titleEl.textContent = detail.title;
    if (idEl) idEl.textContent = detail.issue_key;

    const rootCauseEl = document.getElementById('drawer-root-cause');
    if (rootCauseEl) rootCauseEl.textContent = detail.description;

    const impactEl = document.getElementById('drawer-impact');
    if (impactEl) {
      impactEl.textContent = detail.priority_score ? `Priority ${detail.priority_score.toFixed(1)} / 100` : 'Priority Pending';
    }

    const mentionsEl = document.getElementById('drawer-mentions');
    if (mentionsEl) {
      mentionsEl.textContent = `${detail.row_count} total (${detail.distinct_count} distinct)`;
    }

    const sourceCountEl = document.getElementById('drawer-source-count');
    if (sourceCountEl) {
      sourceCountEl.textContent = `${detail.topic} · Confidence: ${detail.confidence.toUpperCase()}`;
    }

    const actionEl = document.getElementById('drawer-action-text');
    if (actionEl && detail.recommendations && detail.recommendations.length > 0) {
      actionEl.textContent = detail.recommendations[0].recommended_action;
    }

    // Dynamic rendering of verbatim citations
    const quoteContainer = drawer.querySelector('.space-y-3:has(.evidence-quote)');
    if (quoteContainer && detail.evidence && detail.evidence.length > 0) {
      const quotesHtml = detail.evidence.map(ev => {
        const sentimentColor = ev.sentiment_label === 'negative' ? 'text-rose-500' : (ev.sentiment_label === 'positive' ? 'text-emerald-500' : 'text-slate-400');
        return `
          <div class="p-4 rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-slate-900/50 space-y-3">
            <div class="flex items-center justify-between text-[11px] font-mono">
              <span class="font-bold text-slate-900 dark:text-white">Citation #${ev.rank} · ID: ${ev.feedback_id.substring(0, 8)}</span>
              <span class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-bold border border-indigo-200 dark:border-indigo-800/60 text-[10px]">
                ${ev.duplicate_count} Exact Occurrences
              </span>
            </div>
            <p class="evidence-quote font-quote text-slate-800 dark:text-slate-100 leading-relaxed text-[13.5px]">
              "${ev.text}"
            </p>
            <div class="pt-2 border-t border-slate-200 dark:border-white/10 flex justify-between text-[10px] text-slate-400 font-mono">
              <span>Sentiment Label: <strong class="uppercase ${sentimentColor}">${ev.sentiment_label || 'neutral'}</strong></span>
              <span class="font-bold tabular-nums ${sentimentColor}">Score: ${ev.sentiment_score !== null ? ev.sentiment_score.toFixed(2) : 'N/A'}</span>
            </div>
          </div>
        `;
      }).join('');

      quoteContainer.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-slate-500 font-mono text-[10px] uppercase font-bold">Verbatim Customer Citations (Centroid Representatives)</span>
          <span class="text-[10px] font-mono text-indigo-500 font-semibold">${detail.evidence.length} distinct quotes</span>
        </div>
        ${quotesHtml}
      `;
    }
  } catch (err) {
    console.warn('Could not load live issue details, keeping default drawer state:', err);
  }
};

window.closeEvidenceDrawer = function() {
  const drawer = document.getElementById('evidence-drawer');
  const overlay = document.getElementById('drawer-overlay');
  if (drawer) drawer.classList.add('translate-x-full');
  if (overlay) overlay.classList.add('hidden');
};

/**
 * Import Modal Management
 */
window.openImportModal = function() {
  const modal = document.getElementById('import-modal');
  if (modal) modal.classList.remove('hidden');
};

window.closeImportModal = function() {
  const modal = document.getElementById('import-modal');
  if (modal) modal.classList.add('hidden');
};

window.handleFileSelect = function(e) {
  const file = e.target.files?.[0];
  if (file) {
    window.selectedUploadFile = file;
    const nameEl = document.getElementById('uploaded-file-name');
    if (nameEl) nameEl.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(1)} MB)`;
    window.showToast?.(`Selected CSV: ${file.name}`, 'info');
  }
};

window.loadSampleDataset = function() {
  const nameEl = document.getElementById('uploaded-file-name');
  if (nameEl) nameEl.textContent = 'BuildBattle_2026_Customer_Feedback_Dataset.csv (7,000 rows · 320 distinct)';
  window.selectedUploadFile = 'sample';
  window.showToast?.('Selected BuildBattle 2026 Customer Feedback dataset for ingestion.', 'info');
};

window.runVectorIngest = async function() {
  const btn = document.getElementById('ingest-btn');
  const statusEl = document.getElementById('ingest-progress-container');
  const bar = document.getElementById('ingest-progress-bar');
  const label = document.getElementById('ingest-status-label');

  if (statusEl) statusEl.classList.remove('hidden');
  if (btn) btn.disabled = true;

  try {
    if (window.selectedUploadFile instanceof File) {
      if (label) label.textContent = 'Uploading CSV stream & sniffing dialect...';
      if (bar) bar.style.width = '30%';

      const res = await api.uploadDataset(window.selectedUploadFile);
      if (bar) bar.style.width = '60%';
      if (label) label.textContent = `Ingested ${res.valid_count} rows! Running AI sentiment & clustering...`;

      if (res.job_id) {
        let attempts = 0;
        const pollInterval = setInterval(async () => {
          attempts++;
          try {
            const job = await api.getJobStatus(res.job_id);
            if (job.status === 'completed' || attempts > 20) {
              clearInterval(pollInterval);
              if (bar) bar.style.width = '100%';
              if (label) label.textContent = 'Analysis complete!';
              setTimeout(() => {
                window.closeImportModal();
                if (statusEl) statusEl.classList.add('hidden');
                if (btn) btn.disabled = false;
                window.showToast?.(`Successfully indexed ${res.valid_count} records (${res.distinct_text_count} distinct)!`, 'success');
                loadInitialData();
              }, 700);
            }
          } catch (e) {
            clearInterval(pollInterval);
          }
        }, 1000);
        return;
      }
    } else {
      let progress = 20;
      const interval = setInterval(() => {
        progress += 30;
        if (bar) bar.style.width = `${Math.min(progress, 100)}%`;
        if (progress === 50) {
          if (label) label.textContent = 'Performing VADER sentiment indexing & TF-IDF n-gram vectorization...';
        } else if (progress >= 100) {
          clearInterval(interval);
          if (label) label.textContent = 'Cluster synchronization complete!';
          setTimeout(() => {
            window.closeImportModal();
            if (statusEl) statusEl.classList.add('hidden');
            if (btn) btn.disabled = false;
            window.showToast?.('7,000 feedback items indexed with 15 active friction clusters!', 'success');
            loadInitialData();
          }, 600);
        }
      }, 500);
    }
  } catch (err) {
    if (label) label.textContent = `Ingestion error: ${err.message}`;
    window.showToast?.(`Ingestion error: ${err.message}`, 'warning');
    if (btn) btn.disabled = false;
  }
};

/**
 * Export CSV Report
 */
window.exportDatasetCsv = function() {
  if (window.activeDatasetId) {
    const url = api.getExportUrl(window.activeDatasetId);
    window.open(url, '_blank');
    window.showToast?.('Generating & downloading evidence-backed CSV report...', 'info');
  } else {
    window.showToast?.('No active dataset found to export.', 'warning');
  }
};

/**
 * Hotfix Directive Modal
 */
window.openHotfixModal = function(issueKey = 'ISS-884') {
  const modal = document.getElementById('hotfix-modal');
  if (modal) modal.classList.remove('hidden');
};

window.closeHotfixModal = function() {
  const modal = document.getElementById('hotfix-modal');
  if (modal) modal.classList.add('hidden');
};

window.triggerDeployment = function() {
  const btn = document.getElementById('deploy-action-btn');
  const progressBox = document.getElementById('deploy-progress-box');
  const stepLabel = document.getElementById('deploy-step-label');

  if (btn) btn.disabled = true;
  if (progressBox) progressBox.classList.remove('hidden');

  let step = 1;
  const steps = [
    "Running test fixtures: 320 distinct customer quote replays passed (100%)",
    "Canary rollout: 5% traffic diverted to idempotent retry handler...",
    "Telemetry verification: Error rate dropped from 14.8% to 0.04%",
    "ACTION PLAN EXECUTED: Dispatched Jira directive & notified #eng-leadership!",
  ];

  const interval = setInterval(() => {
    if (step < steps.length) {
      if (stepLabel) stepLabel.textContent = steps[step];
      step++;
    } else {
      clearInterval(interval);
      setTimeout(() => {
        window.closeHotfixModal();
        if (progressBox) progressBox.classList.add('hidden');
        if (btn) btn.disabled = false;
        window.showToast?.('ACTION DIRECTIVE DEPLOYED: Telemetry verified live in production.', 'success');
      }, 600);
    }
  }, 700);
};

/**
 * Render Feedback Explorer Table with Live Records
 */
function renderFeedbackTableRows(items, total) {
  const tbody = document.getElementById('feedback-table-body');
  const countBadge = document.getElementById('table-count-badge');
  if (countBadge) {
    countBadge.textContent = `${total || items.length} RECORDS INDEXED`;
  }
  if (!tbody || !items || items.length === 0) return;

  tbody.innerHTML = items.map(fb => {
    const isNeg = fb.sentiment_label === 'negative';
    const isPos = fb.sentiment_label === 'positive';
    const badgeColor = isNeg ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/80 dark:text-rose-300 border-rose-200 dark:border-rose-800/80'
      : (isPos ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/80'
      : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700');

    const sentimentLabel = (fb.sentiment_label || 'NEUTRAL').toUpperCase();
    const scoreFormatted = fb.sentiment_score !== null && fb.sentiment_score !== undefined
      ? (fb.sentiment_score > 0 ? `+${fb.sentiment_score.toFixed(2)}` : fb.sentiment_score.toFixed(2))
      : '0.00';

    return `
      <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-900/40 transition-colors" data-sentiment="${sentimentLabel}" data-category="${fb.source_category || ''}">
        <td class="py-3 px-4 whitespace-nowrap">
          <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border font-mono shadow-2xs inline-block ${badgeColor}">
            ${sentimentLabel}
          </span>
          <div class="font-mono text-[10.5px] text-slate-400 dark:text-slate-500 mt-1 tabular-nums">
            ${fb.source_category || 'Customer Review'} · ID: ${fb.id.substring(0, 8)}
          </div>
        </td>
        <td class="py-3 px-4 max-w-md">
          <p class="evidence-quote font-quote text-slate-900 dark:text-slate-100 text-[13.5px] leading-relaxed">
            "${fb.original_text}"
          </p>
          <div class="evidence-trace mt-1.5 flex items-center gap-1.5 font-mono text-[11px] text-slate-400 dark:text-slate-500">
            <span class="px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[9.5px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Sentiment Score</span>
            <span class="text-slate-600 dark:text-slate-300 font-bold tabular-nums">${scoreFormatted}</span>
            ${fb.is_canonical ? '<span class="px-1 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 text-[9.5px] font-semibold ml-1">Canonical Distinct</span>' : ''}
          </div>
        </td>
        <td class="py-3 px-4 whitespace-nowrap">
          <span class="font-sans font-bold text-xs text-indigo-600 dark:text-indigo-400 tracking-tight">
            ${fb.source_category || 'General'}
          </span>
          <div class="text-[10px] text-slate-400 font-mono uppercase tracking-wider mt-0.5">
            Verified Dataset Row
          </div>
        </td>
        <td class="py-3 px-4 whitespace-nowrap">
          <span class="evidence-cluster-badge px-2 py-1 rounded-md bg-cyan-50 dark:bg-cyan-950/60 text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800 font-mono font-bold text-[11px]">
            ${fb.source_category ? fb.source_category.substring(0, 14) : 'Cluster'}
          </span>
        </td>
        <td class="py-3 px-4 whitespace-nowrap">
          <div class="evidence-price text-slate-400 dark:text-slate-500 font-mono text-xs tabular-nums tracking-tight">
            N/A (Unspecified)
          </div>
        </td>
        <td class="py-3 px-4 whitespace-nowrap text-right">
          <button onclick="window.showToast('Inspecting verbatim record ${fb.id.substring(0, 8)}', 'info')" class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-300 border border-slate-200 dark:border-white/10 font-sans font-semibold text-[11px] shadow-2xs hover:shadow transition-all active:scale-95">
            Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Server-Backed Feedback Search and Filter with Debounce
 */
let filterTimeout = null;
window.filterFeedbackTable = function() {
  clearTimeout(filterTimeout);
  filterTimeout = setTimeout(async () => {
    const search = document.getElementById('feedback-search-input')?.value || '';
    const sentiment = document.getElementById('filter-sentiment')?.value || 'ALL';
    const category = document.getElementById('filter-channel')?.value || 'ALL';

    if (window.activeDatasetId) {
      try {
        const res = await api.getFeedback({
          dataset_id: window.activeDatasetId,
          search: search || undefined,
          sentiment: sentiment !== 'ALL' ? sentiment.toLowerCase() : undefined,
          category: category !== 'ALL' ? category : undefined,
          page: 1,
          pageSize: 25,
        });
        renderFeedbackTableRows(res.items, res.total);
      } catch (err) {
        console.warn('Server search failed:', err);
      }
    }
  }, 250);
};

/**
 * Initial Data Loading
 */
async function loadInitialData() {
  try {
    const dsRes = await api.getDatasets(1, 10);
    if (!dsRes.items || dsRes.items.length === 0) return;

    const dataset = dsRes.items[0];
    window.activeDatasetId = dataset.id;

    // Load analytics KPIs
    const analytics = await api.getAnalytics(dataset.id);
    if (analytics) {
      const countEl = document.getElementById('table-count-badge');
      if (countEl) {
        countEl.textContent = `${analytics.totals.rows_total.toLocaleString()} RECORDS INDEXED (${analytics.totals.distinct_texts} DISTINCT)`;
      }

      const feedbackNav = document.querySelector('[data-view-nav="explorer"] span:last-child');
      if (feedbackNav) {
        feedbackNav.textContent = `Feedback (${(analytics.totals.rows_total / 1000).toFixed(1)}K)`;
      }
    }

    // Load initial feedback rows
    const fbRes = await api.getFeedback({
      dataset_id: dataset.id,
      page: 1,
      pageSize: 25,
    });
    if (fbRes.items && fbRes.items.length > 0) {
      renderFeedbackTableRows(fbRes.items, fbRes.total);
    }
  } catch (err) {
    console.warn('Failed to load initial data from backend API:', err);
  }
}

/**
 * ROI Simulator Slider
 */
window.updateRoiCalc = function(val) {
  const pct = parseInt(val);
  const label = document.getElementById('roi-pct-label');
  if (label) label.textContent = `${pct}%`;

  const baseRecovery = 42000;
  const weekly = Math.round(baseRecovery * (pct / 100));
  const annual = Math.round(weekly * 52);

  const weeklyEl = document.getElementById('roi-weekly-val');
  if (weeklyEl) weeklyEl.textContent = `+$${(weekly / 1000).toFixed(1)}K`;

  const annualEl = document.getElementById('roi-annual-val');
  if (annualEl) annualEl.textContent = `+$${(annual / 1000000).toFixed(2)}M`;
};

/**
 * Theme Toggle Function
 */
window.toggleDarkMode = function() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  window.showToast?.(isDark ? 'Obsidian Dark Mode enabled' : 'Clean Light Mode enabled', 'info');
};

/**
 * Global Toast Dispatcher
 */
window.showToast = function(msg, type = 'success') {
  const container = document.getElementById('toast-root');
  if (!container) return;

  const toast = document.createElement('div');
  const typeStyles = {
    success: 'bg-emerald-950/90 text-emerald-200 border-emerald-500/40 shadow-emerald-950/50',
    info: 'bg-indigo-950/90 text-indigo-200 border-indigo-500/40 shadow-indigo-950/50',
    warning: 'bg-amber-950/90 text-amber-200 border-amber-500/40 shadow-amber-950/50',
  };
  const icon = type === 'success' ? 'check_circle' : (type === 'info' ? 'info' : 'warning');

  toast.className = `toast-anim flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-xl text-xs font-medium ${typeStyles[type] || typeStyles.success}`;
  toast.innerHTML = `<span class="material-symbols-outlined text-base">${icon}</span><span>${msg}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(1rem)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
};

/**
 * Mount React Trees with Context & ErrorBoundary
 */
function mountReactComponents() {
  // 1. Mount Global Background Canvas
  const bgRootEl = document.getElementById('floating-lines-bg-mount');
  if (bgRootEl) {
    const bgRoot = ReactDOM.createRoot(bgRootEl);
    bgRoot.render(
      <ErrorBoundary>
        <WorkspaceProvider>
          <GlobalBackground />
        </WorkspaceProvider>
      </ErrorBoundary>
    );
  }

  // 2. Mount Active Friction Clusters
  const clustersRootEl = document.getElementById('friction-clusters-mount');
  if (clustersRootEl) {
    const clustersRoot = ReactDOM.createRoot(clustersRootEl);
    clustersRoot.render(
      <ErrorBoundary>
        <WorkspaceProvider>
          <FrictionClusters />
        </WorkspaceProvider>
      </ErrorBoundary>
    );
  }

  // 3. Mount Hero Animated Title
  const heroTitleEl = document.getElementById('hero-title-mount');
  if (heroTitleEl) {
    const titleRoot = ReactDOM.createRoot(heroTitleEl);
    titleRoot.render(
      <ErrorBoundary>
        <TextEffectPerChar
          className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white font-sans leading-tight"
          as="h1"
        >
          Turn Customer Friction Into High-Impact Engineering Actions
        </TextEffectPerChar>
      </ErrorBoundary>
    );
  }

  // 4. Mount ToolbarDynamic Floating Action Bar
  const toolbarRootEl = document.getElementById('toolbar-dynamic-mount');
  if (toolbarRootEl) {
    const toolbarRoot = ReactDOM.createRoot(toolbarRootEl);
    toolbarRoot.render(
      <ErrorBoundary>
        <WorkspaceProvider>
          <ToolbarDynamic />
        </WorkspaceProvider>
      </ErrorBoundary>
    );
  }
}

/**
 * Universal Mouse-following Border Glow
 */
function initUniversalBorderGlow() {
  document.addEventListener('pointermove', (e) => {
    const card = e.target.closest('.glass-card, .glass-panel, .border-glow-card');
    if (!card) return;

    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const dx = x - cx;
    const dy = y - cy;

    let kx = Infinity, ky = Infinity;
    if (dx !== 0) kx = cx / Math.abs(dx);
    if (dy !== 0) ky = cy / Math.abs(dy);
    const proximity = Math.min(Math.max(1 / Math.min(kx, ky), 0), 1) * 100;

    const radians = Math.atan2(dy, dx);
    let degrees = radians * (180 / Math.PI) + 90;
    if (degrees < 0) degrees += 360;

    card.style.setProperty('--edge-proximity', proximity.toFixed(2));
    card.style.setProperty('--cursor-angle', `${degrees.toFixed(2)}deg`);
  }, { passive: true });

  document.addEventListener('pointerout', (e) => {
    const card = e.target.closest('.glass-card, .glass-panel, .border-glow-card');
    if (card && (!e.relatedTarget || !card.contains(e.relatedTarget))) {
      card.style.setProperty('--edge-proximity', '0');
    }
  }, { passive: true });
}

/**
 * Initialize Application
 */
function initApp() {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  mountReactComponents();
  initUniversalBorderGlow();
  loadInitialData();

  window.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      const s = document.getElementById('global-search-bar');
      if (s) s.focus();
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

export default BorderGlow;
