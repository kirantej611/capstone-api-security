'use client';

import React from 'react';
import { Search, RefreshCw } from 'lucide-react';

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  onRefresh: () => void;
  isLive: boolean;
}

export default function Header({
  searchQuery,
  setSearchQuery,
  onRefresh,
  isLive,
}: HeaderProps) {
  return (
    <header className="hub-top-header">
      <div className="dashboard-heading">
        <h1>Security Dashboard</h1>
        <span className={`connection-status ${isLive ? 'connected' : 'disconnected'}`}>
          <span className="connection-status-dot" />
          {isLive ? 'Gateway connected' : 'Gateway offline'}
        </span>
      </div>

      <div className="hub-search-box">
        <Search size={16} className="hub-search-icon" />
        <input
          type="text"
          placeholder="Search requests, IPs, or paths..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="hub-search-input"
        />
      </div>

      <div className="hub-user-actions">
        <button
          onClick={onRefresh}
          className="icon-circle-btn"
          title="Refresh telemetry"
          aria-label="Refresh telemetry"
        >
          <RefreshCw size={15} />
        </button>
      </div>
    </header>
  );
}
