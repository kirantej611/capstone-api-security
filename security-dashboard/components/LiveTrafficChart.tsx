'use client';

import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, ShieldBan } from 'lucide-react';

interface Point {
  time: string;
  allowed: number;
  blocked: number;
  latency: number;
}

export default function LiveTrafficChart() {
  const [dataPoints, setDataPoints] = useState<Point[]>([]);
  const [hoveredPoint, setHoveredPoint] = useState<Point | null>(null);

  // Generate initial sliding-window history
  useEffect(() => {
    const initial: Point[] = [];
    const now = Date.now();
    for (let i = 24; i >= 0; i--) {
      const t = new Date(now - i * 2000);
      const allowed = Math.floor(35 + Math.random() * 25);
      const isSpike = i % 6 === 0;
      const blocked = isSpike ? Math.floor(3 + Math.random() * 8) : Math.floor(Math.random() * 2);
      const latency = +(3.2 + Math.random() * 1.5).toFixed(1);
      initial.push({
        time: t.toTimeString().split(' ')[0],
        allowed,
        blocked,
        latency,
      });
    }
    setDataPoints(initial);

    // Live update interval
    const interval = setInterval(() => {
      setDataPoints((prev) => {
        const nextTime = new Date().toTimeString().split(' ')[0];
        const allowed = Math.floor(38 + Math.random() * 20);
        const hasAttack = Math.random() > 0.65;
        const blocked = hasAttack ? Math.floor(2 + Math.random() * 6) : 0;
        const latency = +(3.1 + Math.random() * 1.8).toFixed(1);

        const updated = [
          ...prev.slice(1),
          { time: nextTime, allowed, blocked, latency },
        ];
        return updated;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // SVG dimensions
  const width = 800;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 35, left: 45 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxVal = Math.max(
    ...dataPoints.map((p) => Math.max(p.allowed, p.blocked)),
    70
  );

  const getX = (idx: number) => {
    if (dataPoints.length <= 1) return padding.left;
    return padding.left + (idx / (dataPoints.length - 1)) * chartW;
  };

  const getY = (val: number) => {
    return padding.top + chartH - (val / maxVal) * chartH;
  };

  // Generate SVG Path definitions
  const allowedPath = dataPoints.reduce((acc, p, idx) => {
    const x = getX(idx);
    const y = getY(p.allowed);
    return idx === 0 ? `M ${x},${y}` : `${acc} L ${x},${y}`;
  }, '');

  const allowedArea =
    allowedPath +
    ` L ${getX(dataPoints.length - 1)},${padding.top + chartH} L ${padding.left},${padding.top + chartH} Z`;

  const blockedPath = dataPoints.reduce((acc, p, idx) => {
    const x = getX(idx);
    const y = getY(p.blocked);
    return idx === 0 ? `M ${x},${y}` : `${acc} L ${x},${y}`;
  }, '');

  const blockedArea =
    blockedPath +
    ` L ${getX(dataPoints.length - 1)},${padding.top + chartH} L ${padding.left},${padding.top + chartH} Z`;

  return (
    <div className="glass-panel chart-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <Activity size={18} color="#3b82f6" />
          <div>
            <h3 className="panel-title">Real-time Traffic Volume & Threat Interception</h3>
            <span className="panel-subtitle">Rolling 60s sliding window • 2000ms sampling rate</span>
          </div>
        </div>

        <div className="legend-row font-mono">
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#10b981' }} />
            <span>Allowed Traffic (Clean)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#ef4444', boxShadow: '0 0 8px #ef4444' }} />
            <span>Blocked Threats (AI Shield)</span>
          </div>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', overflow: 'hidden' }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
        >
          <defs>
            <linearGradient id="allowedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="blockedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
            const y = padding.top + chartH * ratio;
            const val = Math.round(maxVal * (1 - ratio));
            return (
              <g key={i}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + chartW}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fill="var(--text-dim)"
                  fontSize="10"
                  fontFamily="var(--font-mono)"
                  textAnchor="end"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Area Fills */}
          <path d={allowedArea} fill="url(#allowedGrad)" />
          <path d={blockedArea} fill="url(#blockedGrad)" />

          {/* Lines */}
          <path
            d={allowedPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d={blockedPath}
            fill="none"
            stroke="#ef4444"
            strokeWidth="2.5"
            filter="url(#glow)"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Points & Interactive Hover Columns */}
          {dataPoints.map((p, idx) => {
            const x = getX(idx);
            const yAllow = getY(p.allowed);
            const yBlock = getY(p.blocked);

            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredPoint(p)}
                onMouseLeave={() => setHoveredPoint(null)}
                style={{ cursor: 'pointer' }}
              >
                {/* Hit area */}
                <rect
                  x={x - 12}
                  y={padding.top}
                  width={24}
                  height={chartH}
                  fill="transparent"
                />

                {p.blocked > 0 && (
                  <circle
                    cx={x}
                    cy={yBlock}
                    r="4"
                    fill="#ef4444"
                    stroke="#fff"
                    strokeWidth="1.5"
                  />
                )}

                {/* X-axis time marks */}
                {idx % 4 === 0 && (
                  <text
                    x={x}
                    y={padding.top + chartH + 20}
                    fill="var(--text-dim)"
                    fontSize="9.5"
                    fontFamily="var(--font-mono)"
                    textAnchor="middle"
                  >
                    {p.time}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoveredPoint && (
          <div
            className="glass-panel"
            style={{
              position: 'absolute',
              top: '1.25rem',
              right: '1.5rem',
              padding: '0.65rem 1rem',
              fontSize: '0.78rem',
              fontFamily: 'var(--font-mono)',
              border: '1px solid var(--border-glow-blue)',
              pointerEvents: 'none',
              zIndex: 10,
            }}
          >
            <div style={{ color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              Timestamp: <span style={{ color: '#fff' }}>{hoveredPoint.time}</span>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <span style={{ color: '#10b981' }}>
                Clean: <strong>{hoveredPoint.allowed} req/s</strong>
              </span>
              <span style={{ color: '#ef4444' }}>
                Blocked: <strong>{hoveredPoint.blocked} req/s</strong>
              </span>
              <span style={{ color: '#60a5fa' }}>
                ML Latency: <strong>{hoveredPoint.latency}ms</strong>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
