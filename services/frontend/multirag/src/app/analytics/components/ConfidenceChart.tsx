"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { QueryLog } from '@/types/api';

interface ChartPoint {
  index: number;
  confidence: number;
  query: string;
  timestamp: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: { value: number; payload: ChartPoint }[];
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-xs shadow-lg max-w-[220px]">
      <p className="font-medium text-foreground mb-1 truncate">{d.query || 'Query ' + d.index}</p>
      <p className="text-foreground-dim">{new Date(d.timestamp).toLocaleString()}</p>
      <p className="mt-1 font-semibold text-accent">{Math.round(d.confidence * 100)}% confidence</p>
    </div>
  );
};

interface ConfidenceChartProps {
  logs: QueryLog[];
  isDark: boolean;
}

export const ConfidenceChart = ({ logs, isDark }: ConfidenceChartProps) => {
  const data: ChartPoint[] = [...logs]
    .reverse()
    .map((log, i) => ({
      index: i + 1,
      confidence: log.confidence,
      query: log.query,
      timestamp: log.timestamp,
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-sm text-foreground-dim italic">
        No queries logged yet
      </div>
    );
  }

  const gridColor = isDark ? '#2a3140' : '#e2e8f0';
  const axisColor = isDark ? '#64748b' : '#94a3b8';
  const lineColor = isDark ? '#2dd4bf' : '#0d9488';

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis
          dataKey="index"
          tick={{ fontSize: 11, fill: axisColor }}
          tickLine={false}
          axisLine={false}
          label={{ value: 'Query #', position: 'insideBottomRight', offset: -4, fontSize: 10, fill: axisColor }}
        />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
          tick={{ fontSize: 11, fill: axisColor }}
          tickLine={false}
          axisLine={false}
          ticks={[0, 0.25, 0.5, 0.75, 1]}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="confidence"
          stroke={lineColor}
          strokeWidth={2}
          dot={{ r: 3, fill: lineColor, strokeWidth: 0 }}
          activeDot={{ r: 5, fill: lineColor, strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
