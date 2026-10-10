'use client';

import React, { useMemo, useState } from 'react';
import { Activity } from 'lucide-react';
import { RecentVerdict } from '../lib/types';

interface Point {
  time: string;
  allowed: number;
  blocked: number;
  other: number;
}

interface LiveTrafficChartProps {
  verdicts: RecentVerdict[];
}

export default function LiveTrafficChart({ verdicts }: LiveTrafficChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<Point | null>(null);
  const dataPoints = useMemo(() => {
    const points = Array.from({ length: 12 }, (_, index) => ({
      time: `${(11 - index) * 5}s`,
      allowed: 0,
      blocked: 0,
      other: 0,
    }));
    const now = Date.now();

    verdicts.forEach((verdict) => {
      const elapsed = now - new Date(verdict.timestamp).getTime();
      if (!Number.isFinite(elapsed) || elapsed < 0 || elapsed >= 60_000) return;

      const point = points[11 - Math.floor(elapsed / 5_000)];
      if (verdict.action === 'BLOCK') point.blocked += 1;
      else if (verdict.action === 'ALLOW') point.allowed += 1;
      else point.other += 1;
    });

    return points;
  }, [verdicts]);

  const hasRecentData = dataPoints.some((point) => point.allowed > 0 || point.blocked > 0 || point.other > 0);
  const width = 800;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 35, left: 45 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const maxVal = Math.max(...dataPoints.map((point) => point.allowed + point.blocked + point.other), 1);
  const getX = (index: number) => padding.left + (index / (dataPoints.length - 1)) * chartW;
  const getY = (value: number) => padding.top + chartH - (value / maxVal) * chartH;
  const allowedPath = dataPoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${getX(index)},${getY(point.allowed)}`)
    .join(' ');
  const blockedPath = dataPoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${getX(index)},${getY(point.blocked)}`)
    .join(' ');
  const otherPath = dataPoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${getX(index)},${getY(point.other)}`)
    .join(' ');

  return (
    <div className="white-card">
      <div className="card-header-row">
        <div className="panel-title-wrap">
          <Activity size={18} color="#3b82f6" />
          <div>
            <h3 className="card-title">Recent request activity</h3>
            <span className="dashboard-subtitle">Available verdicts over the last 60 seconds</span>
          </div>
        </div>
        <div className="traffic-legend">
          <div>
            <span className="legend-dot" style={{ background: '#10b981' }} />
            <span>Allowed</span>
          </div>
          <div>
            <span className="legend-dot" style={{ background: '#ef4444' }} />
            <span>Blocked</span>
          </div>
          <div>
            <span className="legend-dot" style={{ background: '#f59e0b' }} />
            <span>Other</span>
          </div>
        </div>
      </div>

      {hasRecentData ? (
        <div style={{ position: 'relative', width: '100%', overflow: 'hidden' }}>
          <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const y = padding.top + chartH * ratio;
              return (
                <g key={ratio}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={padding.left + chartW}
                    y2={y}
                    stroke="#e2e8f0"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 3}
                    fill="var(--text-muted)"
                    fontSize="9"
                    fontFamily="var(--font-mono)"
                    textAnchor="end"
                  >
                    {Math.round(maxVal * (1 - ratio))}
                  </text>
                </g>
              );
            })}
            <path d={allowedPath} fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" />
            <path d={blockedPath} fill="none" stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round" />
            <path d={otherPath} fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" />
            {dataPoints.map((point, index) => {
              const x = getX(index);
              return (
                <g
                  key={point.time}
                  onMouseEnter={() => setHoveredPoint(point)}
                  onMouseLeave={() => setHoveredPoint(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect x={x - 12} y={padding.top} width={24} height={chartH} fill="transparent" />
                  {index % 2 === 0 && (
                    <text
                      x={x}
                      y={padding.top + chartH + 20}
                      fill="var(--text-muted)"
                      fontSize="9.5"
                      fontFamily="var(--font-mono)"
                      textAnchor="middle"
                    >
                      {point.time} ago
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
          {hoveredPoint && (
            <div className="chart-tooltip">
              <strong>{hoveredPoint.time} ago</strong>
              <span>Allowed: {hoveredPoint.allowed}</span>
              <span>Blocked: {hoveredPoint.blocked}</span>
              <span>Other: {hoveredPoint.other}</span>
            </div>
          )}
        </div>
      ) : (
        <p className="dashboard-empty-state">No gateway verdicts recorded in the last 60 seconds.</p>
      )}
    </div>
  );
}
