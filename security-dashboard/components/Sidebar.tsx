'use client';

import React from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  Zap,
  Cpu,
  Layers,
  ShoppingBag,
  Network,
  Bell,
  User,
  Settings,
  HelpCircle,
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
    { id: 'simulator', label: 'Attack Studio', icon: Zap },
    { id: 'verdicts', label: 'Live Stream', icon: ShieldAlert },
    { id: 'xai', label: 'Explainable AI', icon: Cpu },
    { id: 'blocklist', label: `Redis Blocklist (${blockedCount})`, icon: Layers },
    { id: 'victim', label: 'Victim Store', icon: ShoppingBag },
    { id: 'topology', label: 'System Topology', icon: Network },
  ];

  const otherItems = [
    { id: 'profile', label: 'SOC Profile', icon: User },
    { id: 'settings', label: 'Gateway Settings', icon: Settings },
  ];

  return (
    <aside className="hub-sidebar">
      {/* Brand logo matching SchoolHub / ShieldHub */}
      <div className="hub-brand">
        <div className="hub-brand-icon">
          <ShieldAlert size={19} />
        </div>
        <span className="hub-brand-title">ShieldHub</span>
      </div>

      {/* Main Menu Section */}
      <div className="sidebar-nav-group">
        <div className="sidebar-group-title">MENU</div>
        <ul className="sidebar-nav-list">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id} className="sidebar-nav-item">
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`sidebar-nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon size={17} />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Other Section */}
      <div className="sidebar-nav-group" style={{ marginTop: 'auto' }}>
        <div className="sidebar-group-title">OTHER</div>
        <ul className="sidebar-nav-list">
          {otherItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id} className="sidebar-nav-item">
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`sidebar-nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon size={17} />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
