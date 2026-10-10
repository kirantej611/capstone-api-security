'use client';

import React from 'react';
import { RefreshCw } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  isLive: boolean;
}

export default function Header({
  onRefresh,
  isRefreshing,
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

      <div className="hub-user-actions">
        <button
          onClick={onRefresh}
          className="icon-circle-btn"
          title={isRefreshing ? 'Refreshing telemetry' : 'Refresh telemetry'}
          aria-label={isRefreshing ? 'Refreshing telemetry' : 'Refresh telemetry'}
          disabled={isRefreshing}
        >
          <RefreshCw size={15} className={isRefreshing ? 'icon-spinning' : undefined} />
        </button>
      </div>
    </header>
  );
}
