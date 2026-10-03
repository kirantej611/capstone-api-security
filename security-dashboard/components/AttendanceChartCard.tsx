'use client';

import React from 'react';
import { ChevronDown } from 'lucide-react';

export default function AttendanceChartCard() {
  const days = [
    { name: 'Mon', clean: 68, blocked: 42 },
    { name: 'Tue', clean: 78, blocked: 48 },
    { name: 'Wed', clean: 95, blocked: 72 }, // Active day
    { name: 'Thu', clean: 76, blocked: 68 },
    { name: 'Fri', clean: 62, blocked: 56 },
  ];

  const maxVal = 100;
  const chartHeight = 160;

  return (
    <div className="white-card" style={{ position: 'relative' }}>
      <div className="card-header-row">
        <h3 className="card-title">Traffic Ingress</h3>
        <div className="attendance-filter-chips">
          <button className="select-pill">
            <span>Weekly</span>
            <ChevronDown size={12} />
          </button>
          <button className="select-pill">
            <span>All Routes</span>
            <ChevronDown size={12} />
          </button>
        </div>
      </div>

      {/* Bar Chart Legend */}
      <div className="bar-legend">
        <div>
          <span className="legend-indicator" style={{ background: '#facc15' }} />
          <span>Clean Requests</span>
        </div>
        <div>
          <span className="legend-indicator" style={{ background: '#bae6fd' }} />
          <span>Blocked Attacks</span>
        </div>
      </div>

      {/* Multi-Bar Graph */}
      <div style={{ position: 'relative', marginTop: '1rem' }}>
        {/* Floating Tooltip Pill matching '95% Present' in screenshot */}
        <div className="floating-stat-badge">
          <div>95%</div>
          <div className="floating-stat-sub">Defended</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end', height: `${chartHeight}px`, gap: '1.25rem' }}>
          {/* Y-Axis scale marks */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              height: '100%',
              fontSize: '0.68rem',
              color: 'var(--text-muted)',
              paddingRight: '0.5rem',
            }}
          >
            <span>100</span>
            <span>75</span>
            <span>50</span>
            <span>25</span>
            <span>0</span>
          </div>

          {/* Day Columns */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              justifyContent: 'space-around',
              alignItems: 'flex-end',
              height: '100%',
              borderBottom: '1px solid var(--border-light)',
              paddingBottom: '4px',
            }}
          >
            {days.map((d) => {
              const cleanH = (d.clean / maxVal) * (chartHeight - 20);
              const blockedH = (d.blocked / maxVal) * (chartHeight - 20);

              return (
                <div
                  key={d.name}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  {/* Pair of Bars */}
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '5px' }}>
                    {/* Yellow Bar */}
                    <div
                      style={{
                        width: '10px',
                        height: `${cleanH}px`,
                        background: '#facc15',
                        borderRadius: '999px',
                        transition: 'height 0.4s ease',
                      }}
                      title={`${d.name} Clean: ${d.clean}`}
                    />
                    {/* Sky Blue Bar */}
                    <div
                      style={{
                        width: '10px',
                        height: `${blockedH}px`,
                        background: '#bae6fd',
                        borderRadius: '999px',
                        transition: 'height 0.4s ease',
                      }}
                      title={`${d.name} Blocked: ${d.blocked}`}
                    />
                  </div>

                  {/* Day label */}
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {d.name}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
