import React from 'react';
import { BorderGlow } from '../ui';
import { useIssues } from '../../hooks';
import { useWorkspace } from '../../context/WorkspaceContext';

/**
 * Friction Clusters Feature Component
 * Displays prioritized customer friction groups with live priority badges & citation counters.
 */
export default function FrictionClusters() {
  const { theme, openDrawer, setHotfixModalOpen } = useWorkspace();
  const { issues, loading, error } = useIssues({ pageSize: 6 });
  const isDark = theme === 'dark';
  const cardBg = isDark ? '#121A2D' : '#ffffff';

  // Fallback demo issues if backend hasn't finished seeding or offline
  const displayIssues = issues.length > 0 ? issues : [
    {
      id: "ISS-884",
      issue_key: "ISS-884",
      title: "Stripe 3DS Verification Timeout (PSD2 Handshake)",
      description: "Barclaycard / BNP Paribas 3D Secure challenge window stalls after 15s. Session drops customers back to home cart with failed auth.",
      topic: "Operational Issues",
      row_count: 342,
      distinct_count: 14,
      priority_score: 88.5,
      confidence: "high",
      status: "open",
    },
    {
      id: "ISS-885",
      issue_key: "ISS-885",
      title: "Carrier Delivery Tracking Link 404 Desync",
      description: "FedEx automated dispatch notification URL encoding drops regional carrier tokens, routing customer links to 404 page.",
      topic: "Customer Service",
      row_count: 194,
      distinct_count: 9,
      priority_score: 74.2,
      confidence: "medium",
      status: "open",
    },
    {
      id: "ISS-886",
      issue_key: "ISS-886",
      title: "Mobile Bag Tray Unresponsive on iOS 17.4",
      description: "SwiftUI Sheet modal presentation proxy freezes when invoked from bottom nav on iPhone 15 devices.",
      topic: "Product Feedback",
      row_count: 118,
      distinct_count: 7,
      priority_score: 68.0,
      confidence: "medium",
      status: "open",
    },
  ];

  const getThemeProps = (idx, priorityScore) => {
    if (priorityScore >= 80 || idx === 0) {
      return {
        glowColor: "340 85 65",
        colors: ['#f43f5e', '#6366f1', '#06b6d4'],
        badgeBg: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border-rose-300 dark:border-rose-800',
        badgeText: 'CRITICAL BLOCKER',
        volColor: 'text-rose-600 dark:text-rose-400',
      };
    } else if (priorityScore >= 60 || idx === 1) {
      return {
        glowColor: "40 90 60",
        colors: ['#f59e0b', '#fbbf24', '#06b6d4'],
        badgeBg: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-300 dark:border-amber-800',
        badgeText: 'HIGH SEVERITY',
        volColor: 'text-amber-600 dark:text-amber-400',
      };
    } else {
      return {
        glowColor: "250 85 65",
        colors: ['#6366f1', '#a855f7', '#38bdf8'],
        badgeBg: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300 border-indigo-300 dark:border-indigo-800',
        badgeText: 'PRIORITY ISSUE',
        volColor: 'text-indigo-600 dark:text-indigo-400',
      };
    }
  };

  return (
    <div className="space-y-4">
      {displayIssues.map((issue, idx) => {
        const themeProps = getThemeProps(idx, issue.priority_score || 70);
        const issueKey = issue.issue_key || issue.id;

        return (
          <BorderGlow
            key={issue.id || idx}
            edgeSensitivity={20}
            glowColor={themeProps.glowColor}
            backgroundColor={cardBg}
            borderRadius={16}
            glowRadius={36}
            glowIntensity={idx === 0 ? 1.3 : 1.2}
            coneSpread={28}
            animated={idx === 0}
            colors={themeProps.colors}
            className="shadow-sm transition-all"
          >
            <div className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="w-full">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${themeProps.badgeBg}`}>
                      {themeProps.badgeText}
                    </span>
                    <span className="font-mono text-xs text-slate-500 dark:text-slate-400">{issueKey}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      {issue.topic}
                    </span>
                    {issue.priority_score !== undefined && (
                      <span className="ml-auto font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-200 dark:border-indigo-800">
                        Priority: {issue.priority_score.toFixed(1)}/100
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-1.5 group-hover:text-indigo-500 transition-colors">
                    {issue.title}
                  </h3>

                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                    {issue.description}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200/80 dark:border-white/10 flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-3 font-mono">
                  <span className={`${themeProps.volColor} font-bold`}>
                    {issue.row_count} total rows ({issue.distinct_count} distinct)
                  </span>
                  <span className="text-slate-500 dark:text-slate-400 text-[11px]">
                    Status: <strong className="uppercase text-slate-800 dark:text-slate-200">{issue.status}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openDrawer(issue.id || issueKey)}
                    className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-[11px] transition-colors"
                  >
                    Evidence
                  </button>
                  <button
                    onClick={() => {
                      if (window.openHotfixModal) {
                        window.openHotfixModal(issue.id || issueKey);
                      } else {
                        setHotfixModalOpen(true);
                      }
                    }}
                    className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[11px] shadow-sm transition-all"
                  >
                    Action Plan
                  </button>
                </div>
              </div>
            </div>
          </BorderGlow>
        );
      })}
    </div>
  );
}
