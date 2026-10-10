'use client';

import React from 'react';
import Link from 'next/link';
import {
  LayoutDashboard,
  ShieldAlert,
  Zap,
  Cpu,
  Layers,
  ShoppingBag,
  Network,
  FlaskConical,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  blockedCount: number;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  blockedCount,
}: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'verdicts', label: 'Live Stream', icon: ShieldAlert },
    { id: 'simulator', label: 'Attack Studio', icon: Zap },
    { id: 'xai', label: 'Explainable AI', icon: Cpu },
    { id: 'blocklist', label: `Redis Blocklist (${blockedCount})`, icon: Layers },
    { id: 'topology', label: 'System Topology', icon: Network },
  ];

  return (
    <aside className="hub-sidebar">
      <div className="hub-brand">
        <div className="hub-brand-icon">
          <ShieldAlert size={19} />
        </div>
        <span className="hub-brand-title">ShieldHub</span>
      </div>

      <div className="sidebar-nav-group">
        <div className="sidebar-group-title">SECURITY</div>
        <ul className="sidebar-nav-list">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id} className="sidebar-nav-item">
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`sidebar-nav-link ${isActive ? 'active' : ''}`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon size={17} />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="sidebar-nav-group" style={{ marginTop: '1.25rem' }}>
        <div className="sidebar-group-title">SEPARATE APPS</div>
        <ul className="sidebar-nav-list">
          <li className="sidebar-nav-item">
            <Link href="/shop" className="sidebar-nav-link">
              <ShoppingBag size={17} />
              <span>Customer store</span>
            </Link>
          </li>
          <li className="sidebar-nav-item">
            <Link href="/demo" className="sidebar-nav-link">
              <FlaskConical size={17} />
              <span>Shield vs direct demo</span>
            </Link>
          </li>
        </ul>
      </div>
    </aside>
  );
}
