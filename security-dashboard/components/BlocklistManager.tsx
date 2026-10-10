'use client';

import React, { useState } from 'react';
import { Layers, Plus, Trash2 } from 'lucide-react';
import { BlockedIPEntry } from '../lib/types';
import { addIpToBlocklist, removeIpFromBlocklist } from '../lib/api';

interface BlocklistManagerProps {
  blockedIps: BlockedIPEntry[];
  onRefreshList: () => void;
  isLive: boolean;
}

export default function BlocklistManager({
  blockedIps,
  onRefreshList,
  isLive,
}: BlocklistManagerProps) {
  const [newIp, setNewIp] = useState('');
  const [newReason, setNewReason] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [isRemoving, setIsRemoving] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIp.trim()) return;
    setIsAdding(true);
    setActionError(null);
    try {
      await addIpToBlocklist(newIp.trim(), newReason.trim());
      setNewIp('');
      onRefreshList();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Could not add IP');
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemove = async (ip: string) => {
    setIsRemoving(ip);
    setActionError(null);
    try {
      await removeIpFromBlocklist(ip);
      onRefreshList();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Could not remove IP');
    } finally {
      setIsRemoving(null);
    }
  };

  return (
    <div className="white-card">
      <div className="card-header-row" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 className="card-title">IP blocklist</h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            {isLive ? 'Entries reported by the connected gateway.' : 'Gateway unavailable. Blocklist changes are not applied locally.'}
          </span>
        </div>

        <span className={`hub-badge ${isLive ? 'hub-badge-allow' : 'hub-badge-rate'} font-mono`}>
          {blockedIps.length} active {blockedIps.length === 1 ? 'entry' : 'entries'}
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
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {blockedIps.map((entry) => (
              <tr key={entry.ip}>
                <td className="font-mono" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {entry.ip}
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{entry.reason || 'Not provided by gateway'}</td>
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
            {blockedIps.length === 0 && (
              <tr>
                <td colSpan={3} className="dashboard-empty-state">
                  No blocked IP entries are available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
