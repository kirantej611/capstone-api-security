'use client';

import React from 'react';
import { Users, Shield } from 'lucide-react';
import { RecentVerdict } from '../lib/types';

interface DonutChartCardProps {
  verdicts: RecentVerdict[];
}

export default function DonutChartCard({ verdicts }: DonutChartCardProps) {
  // SVG concentric rings calculation
  const size = 180;
  const strokeWidth = 14;

  // Outer ring (Sky Blue) -> SQLi / Critical threats
  const outerRadius = 70;
  const outerCircumference = 2 * Math.PI * outerRadius;
  const outerPercent = 0.68; // 68%
  const outerDashoffset = outerCircumference * (1 - outerPercent);

  // Inner ring (Sunny Yellow) -> XSS & Application attacks
  const innerRadius = 48;
  const innerCircumference = 2 * Math.PI * innerRadius;
  const innerPercent = 0.52; // 52%
  const innerDashoffset = innerCircumference * (1 - innerPercent);

  return (
    <div className="white-card">
      <div className="card-header-row">
        <h3 className="card-title">Threat Vectors</h3>
        <button className="card-dots-btn">•••</button>
      </div>

      {/* Concentric Double-Ring Donut matching screenshot */}
      <div className="donut-center-wrap">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background track for outer ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={outerRadius}
            fill="none"
            stroke="#e0f2fe"
            strokeWidth={strokeWidth}
          />
          {/* Outer Ring: Sky Blue */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={outerRadius}
            fill="none"
            stroke="#38bdf8"
            strokeWidth={strokeWidth}
            strokeDasharray={outerCircumference}
            strokeDashoffset={outerDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />

          {/* Background track for inner ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={innerRadius}
            fill="none"
            stroke="#fef9c3"
            strokeWidth={strokeWidth}
          />
          {/* Inner Ring: Sunny Yellow */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={innerRadius}
            fill="none"
            stroke="#facc15"
            strokeWidth={strokeWidth}
            strokeDasharray={innerCircumference}
            strokeDashoffset={innerDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </svg>

        {/* Center Icons (stylized icons in blue and yellow matching template) */}
        <div
          style={{
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
          }}
        >
          <div
            style={{
              width: '16px',
              height: '24px',
              background: '#38bdf8',
              borderRadius: '8px',
            }}
          />
          <div
            style={{
              width: '16px',
              height: '20px',
              background: '#facc15',
              borderRadius: '8px',
            }}
          />
        </div>
      </div>

      {/* Bottom Values matching 45.414 Boys (47%) and 40.270 Girls (53%) */}
      <div className="donut-legend-row">
        <div className="donut-legend-item">
          <span className="donut-legend-val">45,414</span>
          <span className="donut-legend-lbl">Critical SQLi (47%)</span>
        </div>

        <div className="donut-legend-item">
          <span className="donut-legend-val">40,270</span>
          <span className="donut-legend-lbl">XSS & Web (53%)</span>
        </div>
      </div>
    </div>
  );
}
