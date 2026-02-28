"use client";

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { AnalyticsCard } from './components/AnalyticsCard';
import { QueryTable } from './components/QueryTable';
import type { EvalSummary, QueryLog } from '@/types/api';
import { API_BASE_URL } from '../test-post/utils/constants';

const ConfidenceChart = dynamic(
  () => import('./components/ConfidenceChart').then((m) => m.ConfidenceChart),
  { ssr: false, loading: () => <div className="h-[200px] flex items-center justify-center text-sm text-foreground-dim">Loading chart...</div> }
);

const EVAL_SUMMARY = `${API_BASE_URL}/eval/summary`;
const EVAL_LOGS = `${API_BASE_URL}/eval/logs?limit=50`;

const BackIcon = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 12H5M12 5l-7 7 7 7" />
  </svg>
);

const RefreshIcon = ({ spinning }: { spinning: boolean }) => (
  <svg className={`h-4 w-4 ${spinning ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [logs, setLogs] = useState<QueryLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const dark = localStorage.getItem('theme') !== 'light';
    setIsDark(dark);
  }, []);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [summaryRes, logsRes] = await Promise.all([
        fetch(EVAL_SUMMARY),
        fetch(EVAL_LOGS),
      ]);

      if (!summaryRes.ok || !logsRes.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const [summaryData, logsData] = await Promise.all([
        summaryRes.json() as Promise<EvalSummary>,
        logsRes.json() as Promise<{ logs: QueryLog[] }>,
      ]);

      setSummary(summaryData);
      setLogs(logsData.logs ?? []);
    } catch {
      setError('Could not connect to backend. Make sure the server is running.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const hallucinationAccent = (rate: number) =>
    rate >= 0.3 ? 'red' : rate >= 0.1 ? 'amber' : 'green';

  const confidenceAccent = (avg: number) =>
    avg >= 0.7 ? 'green' : avg >= 0.4 ? 'amber' : 'red';

  return (
    <main className="min-h-screen bg-background pt-10 pb-20 px-4">
      <div className="w-full max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/test-post"
              className="flex items-center gap-1.5 text-sm text-foreground-dim hover:text-foreground transition-colors"
            >
              <BackIcon />
              Back
            </Link>
            <span className="text-border">|</span>
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-foreground">System Analytics</h1>
              <p className="text-xs text-foreground-dim mt-0.5">Live metrics from the SQLite query log</p>
            </div>
          </div>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            aria-label="Refresh data"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-foreground-dim hover:text-foreground hover:bg-surface border border-border transition-colors disabled:opacity-50"
          >
            <RefreshIcon spinning={refreshing} />
            Refresh
          </button>
        </div>

        {/* Loading skeleton */}
        {loading && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-xl border border-border bg-surface px-5 py-4 h-24 animate-pulse" />
            ))}
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 px-5 py-4 text-sm">
            {error}
          </div>
        )}

        {/* Summary cards */}
        {summary && !loading && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <AnalyticsCard
              label="Total Queries"
              value={summary.total_queries}
              sub="all time"
            />
            <AnalyticsCard
              label="Avg Confidence"
              value={`${Math.round(summary.avg_confidence * 100)}%`}
              sub="across all queries"
              accent={confidenceAccent(summary.avg_confidence)}
            />
            <AnalyticsCard
              label="Hallucination Rate"
              value={`${Math.round(summary.hallucination_rate * 100)}%`}
              sub="low groundedness"
              accent={hallucinationAccent(summary.hallucination_rate)}
            />
            <AnalyticsCard
              label="Avg Latency"
              value={`${(summary.avg_latency_ms / 1000).toFixed(1)}s`}
              sub="end-to-end"
            />
          </div>
        )}

        {/* Confidence over time chart */}
        {!loading && (
          <div className="rounded-xl border border-border bg-surface p-5">
            <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider mb-4">
              Confidence Over Time
            </p>
            <ConfidenceChart logs={logs} isDark={isDark} />
          </div>
        )}

        {/* Recent queries table */}
        {!loading && (
          <div className="rounded-xl border border-border bg-surface p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-medium text-foreground-dim uppercase tracking-wider">
                Recent Queries
              </p>
              <span className="text-xs text-foreground-dim tabular-nums">
                {logs.length} shown
              </span>
            </div>
            <QueryTable logs={logs} />
          </div>
        )}
      </div>
    </main>
  );
}
