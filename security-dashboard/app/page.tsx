'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import KpiCards from '../components/KpiCards';
import LiveTrafficChart from '../components/LiveTrafficChart';
import ThreatRadar from '../components/ThreatRadar';
import VerdictFeed from '../components/VerdictFeed';
import VerdictDetailModal from '../components/VerdictDetailModal';
import AttackSimulatorPanel from '../components/AttackSimulatorPanel';
import BlocklistManager from '../components/BlocklistManager';
import TopologyMap from '../components/TopologyMap';
import ExplainabilityPanel from '../components/ExplainabilityPanel';

import {
  fetchBlocklist,
  fetchGatewayStats,
  fetchRecentVerdicts,
  EMPTY_STATS,
} from '../lib/api';
import { BlockedIPEntry, GatewayStats, RecentVerdict } from '../lib/types';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [stats, setStats] = useState<GatewayStats>(EMPTY_STATS);
  const [verdicts, setVerdicts] = useState<RecentVerdict[]>([]);
  const [blockedIps, setBlockedIps] = useState<BlockedIPEntry[]>([]);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [isBlocklistLive, setIsBlocklistLive] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [selectedVerdict, setSelectedVerdict] = useState<RecentVerdict | null>(null);

  const refreshTelemetry = useCallback(async () => {
    const statsRes = await fetchGatewayStats();
    const verdictsRes = await fetchRecentVerdicts();
    const blocklistRes = await fetchBlocklist();

    setStats(statsRes.data);
    setVerdicts(verdictsRes.data);
    setBlockedIps(blocklistRes.data);
    setIsLive(statsRes.isLive);
    setIsBlocklistLive(blocklistRes.isLive);
  }, []);

  const handleManualRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshTelemetry();
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshTelemetry]);

  useEffect(() => {
    refreshTelemetry();
    const interval = setInterval(refreshTelemetry, 3000);
    return () => clearInterval(interval);
  }, [refreshTelemetry]);

  return (
    <div className="hub-layout">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        blockedCount={blockedIps.length}
      />

      {/* Main Content Area */}
      <main className="hub-main">
        <Header
          onRefresh={handleManualRefresh}
          isRefreshing={isRefreshing}
          isLive={isLive}
        />

        {/* Dashboard overview */}
        {activeTab === 'dashboard' && (
          <>
            <KpiCards stats={stats} />
            <div className="dashboard-insights-grid">
              <LiveTrafficChart verdicts={verdicts} />
              <ThreatRadar verdicts={verdicts} />
            </div>
            <VerdictFeed
              verdicts={verdicts}
              onSelectVerdict={(v) => setSelectedVerdict(v)}
              isLive={isLive}
            />
          </>
        )}

        {/* 2. ATTACK STUDIO VIEW */}
        {activeTab === 'simulator' && <AttackSimulatorPanel />}

        {/* 3. LIVE STREAM VIEW */}
        {activeTab === 'verdicts' && (
          <VerdictFeed
            verdicts={verdicts}
            onSelectVerdict={(v) => setSelectedVerdict(v)}
            isLive={isLive}
          />
        )}

        {/* 4. EXPLAINABLE AI VIEW */}
        {activeTab === 'xai' && (
          <ExplainabilityPanel verdicts={verdicts} isLive={isLive} />
        )}

        {/* 5. REDIS BLOCKLIST VIEW */}
        {activeTab === 'blocklist' && (
          <BlocklistManager
            blockedIps={blockedIps}
            onRefreshList={refreshTelemetry}
            isLive={isBlocklistLive}
          />
        )}

        {/* 6. SYSTEM TOPOLOGY VIEW */}
        {activeTab === 'topology' && <TopologyMap />}

      </main>

      {/* Forensic Dossier Modal */}
      <VerdictDetailModal
        verdict={selectedVerdict}
        onClose={() => setSelectedVerdict(null)}
        onBlockIpSuccess={() => refreshTelemetry()}
      />
    </div>
  );
}
