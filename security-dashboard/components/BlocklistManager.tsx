'use client';

import React, { useState } from 'react';
import { Layers, Plus, Trash2, Timer } from 'lucide-react';
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
    <div className="white-card">
      <div className="card-header-row" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 className="card-title">Redis In-Memory Blocklist & Perimeter Defense</h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            O(1) lookup in Redis • Drops malicious requests at port 8080 ingress before calling ML engine
          </span>
        </div>

        <span className="hub-badge hub-badge-allow font-mono">
          REDIS :6379 CONNECTED ({blockedIps.length} active bans)
        </span>
      </div>

      {/* Add New IP Form */}
      <form
        onSubmit={handleAdd}
        style={{
          display: 'flex',
          gap: '0.75rem',
          marginBottom: '1.25rem',
          flexWrap: 'wrap',
          background: '#f8fafc',
          padding: '1rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-light)',
        }}
      >
        <input
          type="text"
          placeholder="IPv4 or IPv6 address (e.g. 198.51.100.42)"
          value={newIp}
          onChange={(e) => setNewIp(e.target.value)}
          className="hub-search-input font-mono"
          style={{ width: '220px', paddingLeft: '1rem' }}
          required
        />

        <input
          type="text"
          placeholder="Reason (e.g. Excessive SQLi queries)"
          value={newReason}
          onChange={(e) => setNewReason(e.target.value)}
          className="hub-search-input"
          style={{ width: '260px', paddingLeft: '1rem' }}
        />

        <button type="submit" className="hub-btn-primary" disabled={isAdding}>
          <Plus size={14} />
          <span>{isAdding ? 'Adding...' : 'Add IP to Blocklist'}</span>
        </button>
      </form>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="hub-table">
          <thead>
            <tr>
              <th>Blocked IP Address</th>
              <th>Trigger Reason</th>
              <th>Enforcement Severity</th>
              <th>Timestamp</th>
              <th>TTL Remaining</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {blockedIps.map((entry) => (
              <tr key={entry.ip}>
                <td className="font-mono" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {entry.ip}
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{entry.reason}</td>
                <td>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: entry.severity === 'CRITICAL' ? '#fee2e2' : '#fef3c7',
                      color: entry.severity === 'CRITICAL' ? '#dc2626' : '#d97706',
                    }}
                  >
                    {entry.severity || 'HIGH'}
                  </span>
                </td>
                <td className="font-mono" style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>
                  {entry.blocked_at.slice(0, 19).replace('T', ' ')}
                </td>
                <td className="font-mono" style={{ color: '#0284c7', fontSize: '0.76rem' }}>
                  <Timer size={12} style={{ display: 'inline', marginRight: '3px' }} />
                  {entry.ttl_remaining_seconds}s
                </td>
                <td>
                  <button
                    className="hub-btn-danger"
                    style={{ padding: '0.25rem 0.65rem', fontSize: '0.72rem' }}
                    onClick={() => handleRemove(entry.ip)}
                    disabled={isRemoving === entry.ip}
                  >
                    <Trash2 size={12} />
                    <span>{isRemoving === entry.ip ? 'Unblocking...' : 'Unblock'}</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
