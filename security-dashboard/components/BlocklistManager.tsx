'use client';

import React, { useState } from 'react';
import { Layers, Plus, Trash2, ShieldAlert, Timer, Database, Server } from 'lucide-react';
import { BlockedIPEntry } from '../lib/types';
import { addIpToBlocklist, removeIpFromBlocklist } from '../lib/api';

interface BlocklistManagerProps {
  blockedIps: BlockedIPEntry[];
  onRefreshList: () => void;
}

export default function BlocklistManager({
  blockedIps,
  onRefreshList,
}: BlocklistManagerProps) {
  const [newIp, setNewIp] = useState('');
  const [newReason, setNewReason] = useState('Manual SOC Action');
  const [isAdding, setIsAdding] = useState(false);
  const [isRemoving, setIsRemoving] = useState<string | null>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIp.trim()) return;
    setIsAdding(true);
    try {
      await addIpToBlocklist(newIp.trim(), newReason.trim());
      setNewIp('');
      onRefreshList();
    } catch (err) {
      console.error(err);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemove = async (ip: string) => {
    setIsRemoving(ip);
    try {
      await removeIpFromBlocklist(ip);
      onRefreshList();
    } catch (err) {
      console.error(err);
    } finally {
      setIsRemoving(null);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '1rem',
        }}
      >
        <div className="panel-title-wrap">
          <Layers size={20} color="#f59e0b" />
          <div>
            <h2 className="panel-title" style={{ fontSize: '1.15rem' }}>
              Redis High-Velocity IP Blocklist & Perimeter Defense
            </h2>
            <span className="panel-subtitle">
              Sub-millisecond O(1) lookup • Blocks hostile IPs at gateway ingress prior to ML inference
            </span>
          </div>
        </div>

        <div className="status-pill font-mono">
          <Server size={14} color="#10b981" />
          <span>REDIS :6379 SYNCED ({blockedIps.length} active entries)</span>
        </div>
      </div>

      {/* Manual Add Form */}
      <form
        onSubmit={handleAdd}
        style={{
          display: 'flex',
          gap: '0.75rem',
          marginBottom: '1.25rem',
          flexWrap: 'wrap',
          background: 'rgba(255, 255, 255, 0.02)',
          padding: '0.85rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <input
          type="text"
          placeholder="IPv4 or IPv6 address (e.g. 198.51.100.42)"
          value={newIp}
          onChange={(e) => setNewIp(e.target.value)}
          className="search-input"
          style={{ width: '220px', padding: '0.45rem 0.75rem' }}
          required
        />

        <input
          type="text"
          placeholder="Block reason (e.g. Suspicious Scanner)"
          value={newReason}
          onChange={(e) => setNewReason(e.target.value)}
          className="search-input"
          style={{ width: '280px', padding: '0.45rem 0.75rem' }}
        />

        <button
          type="submit"
          className="btn-primary"
          disabled={isAdding}
          style={{ padding: '0.45rem 1rem' }}
        >
          <Plus size={14} />
          <span>{isAdding ? 'Adding...' : 'Add to Redis Blocklist'}</span>
        </button>
      </form>

      {/* Table of Blocked IPs */}
      <div className="table-wrap">
        <table className="verdict-table">
          <thead>
            <tr>
              <th>Blocked IP Address</th>
              <th>Trigger Reason</th>
              <th>Enforcement Severity</th>
              <th>Timestamp</th>
              <th>TTL Remaining</th>
              <th>Perimeter Action</th>
            </tr>
          </thead>
          <tbody>
            {blockedIps.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>
                  Blocklist is currently clean. No active bans.
                </td>
              </tr>
            ) : (
              blockedIps.map((entry) => (
                <tr key={entry.ip}>
                  <td className="font-mono" style={{ color: '#fff', fontWeight: 600 }}>
                    {entry.ip}
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{entry.reason}</td>
                  <td>
                    <span className={`risk-pill risk-${entry.severity || 'HIGH'}`}>
                      {entry.severity || 'HIGH'}
                    </span>
                  </td>
                  <td className="font-mono" style={{ color: 'var(--text-dim)', fontSize: '0.74rem' }}>
                    {entry.blocked_at.slice(0, 19).replace('T', ' ')}
                  </td>
                  <td className="font-mono" style={{ color: '#93c5fd', fontSize: '0.76rem' }}>
                    <Timer size={12} style={{ display: 'inline', marginRight: '4px' }} />
                    {entry.ttl_remaining_seconds}s
                  </td>
                  <td>
                    <button
                      className="btn-danger"
                      style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }}
                      onClick={() => handleRemove(entry.ip)}
                      disabled={isRemoving === entry.ip}
                    >
                      <Trash2 size={12} />
                      <span>{isRemoving === entry.ip ? 'Unblocking...' : 'Unblock'}</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
