'use client';

import React from 'react';
import { Search, Bell, Moon, Play, Pause, RefreshCw } from 'lucide-react';

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  isStreaming: boolean;
  setIsStreaming: (val: boolean | ((prev: boolean) => boolean)) => void;
  onRefresh: () => void;
  isLive: boolean;
}

export default function Header({
  searchQuery,
  setSearchQuery,
  isStreaming,
  setIsStreaming,
  onRefresh,
  isLive,
}: HeaderProps) {
  return (
    <header className="hub-top-header">
      {/* Search pill matching the template */}
      <div className="hub-search-box">
        <Search size={16} className="hub-search-icon" />
        <input
          type="text"
          placeholder="Search requests, IPs, CVEs..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="hub-search-input"
        />
      </div>

      {/* Right User & Notification Actions */}
      <div className="hub-user-actions">
        {/* Stream Toggle */}
        <button
          onClick={() => setIsStreaming((prev) => !prev)}
          className="icon-circle-btn"
          title={isStreaming ? 'Pause live stream' : 'Resume live stream'}
        >
          {isStreaming ? <Pause size={15} color="#0284c7" /> : <Play size={15} color="#16a34a" />}
        </button>

        {/* Refresh */}
        <button onClick={onRefresh} className="icon-circle-btn" title="Refresh metrics">
          <RefreshCw size={15} />
        </button>

        {/* Bell with red notification badge */}
        <button className="icon-circle-btn" title="Alerts & Notifications">
          <Bell size={16} />
          <span className="notification-badge" />
        </button>

        {/* User Chip matching template (Linda Adora / Admin) */}
        <div className="hub-user-chip">
          <div className="hub-user-info">
            <span className="hub-user-name">Linda Adora</span>
            <span className="hub-user-role">SOC Admin</span>
          </div>
          {/* Avatar representation */}
          <div
            className="hub-avatar"
            style={{
              background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 700,
              fontSize: '0.85rem',
            }}
          >
            LA
          </div>
        </div>
      </div>
    </header>
  );
}
