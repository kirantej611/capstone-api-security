'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Activity,
  Zap,
  Cpu,
  Layers,
  ShoppingBag,
  Network,
  Clock,
  Radio,
  Play,
  Pause,
  RefreshCw,
} from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isLive: boolean;
  isStreaming: boolean;
  setIsStreaming: (val: boolean | ((prev: boolean) => boolean)) => void;
  onRefresh: () => void;
  blockedCount: number;
}

export default function Header({
  activeTab,
  setActiveTab,
  isLive,
  isStreaming,
  setIsStreaming,
  onRefresh,
  blockedCount,
}: HeaderProps) {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toTimeString().split(' ')[0] + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'command-center', label: 'SOC Command Center', icon: Activity },
    { id: 'simulator', label: 'Attack Simulation Studio', icon: Zap },
    { id: 'xai', label: 'Explainable AI (XAI)', icon: Cpu },
    { id: 'blocklist', label: `Redis Blocklist (${blockedCount})`, icon: Layers },
    { id: 'victim', label: 'Victim Storefront', icon: ShoppingBag },
    { id: 'topology', label: 'System Topology', icon: Network },
  ];

  return (
    <header className="soc-header">
      <div className="brand-section">
        <div className="shield-logo-wrap">
          <ShieldAlert size={26} color="#3b82f6" />
        </div>
        <div>
          <h1 className="brand-title">
            AEGIS-AI SHIELD
            <span style={{ fontSize: '0.65rem', padding: '2px 8px', background: 'rgba(59,130,246,0.2)', color: '#60a5fa', borderRadius: '4px', border: '1px solid rgba(59,130,246,0.3)', fontFamily: 'var(--font-mono)' }}>
              v2.4 PROD
            </span>
          </h1>
          <p className="brand-sub">Neural API Defense System • Gateway :8080 • ML :8001</p>
        </div>
      </div>

      <nav className="nav-tabs">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`nav-tab-btn ${isActive ? 'active' : ''}`}
            >
              <Icon size={15} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="header-actions">
        <div className="status-pill">
          <span className={`status-indicator ${isLive ? 'live' : 'sim'}`} />
          <span>{isLive ? 'GATEWAY: ONLINE (:8080)' : 'SIMULATION MODE (ACTIVE)'}</span>
        </div>

        <button
          onClick={() => setIsStreaming((prev) => !prev)}
          className="btn-secondary"
          title={isStreaming ? 'Pause real-time streaming' : 'Resume real-time streaming'}
          style={{ padding: '0.35rem 0.65rem' }}
        >
          {isStreaming ? (
            <>
              <Pause size={13} color="#f59e0b" />
              <span style={{ fontSize: '0.74rem' }}>Live Stream</span>
            </>
          ) : (
            <>
              <Play size={13} color="#10b981" />
              <span style={{ fontSize: '0.74rem' }}>Paused</span>
            </>
          )}
        </button>

        <button
          onClick={onRefresh}
          className="btn-secondary"
          title="Force refresh metrics"
          style={{ padding: '0.35rem 0.55rem' }}
        >
          <RefreshCw size={13} />
        </button>

        <div className="status-pill" style={{ color: 'var(--text-dim)' }}>
          <Clock size={12} />
          <span>{timeStr || '00:00:00 UTC'}</span>
        </div>
      </div>
    </header>
  );
}
