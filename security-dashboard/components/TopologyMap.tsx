'use client';

import React, { useState } from 'react';
import { Network, Shield, Cpu, Database, Server, Radio } from 'lucide-react';

export default function TopologyMap() {
  const [activeNode, setActiveNode] = useState<string>('gateway');

  const nodes = [
    {
      id: 'clients',
      title: 'Clients & Simulation',
      role: 'Member 2 (Simulation)',
      tech: 'Python Traffic Generator',
      port: 'Ingress Stream',
      desc: 'Generates normal browsing, SQL injections on login, XSS reviews, and credential stuffing bursts.',
      icon: Radio,
      color: '#eab308',
    },
    {
      id: 'gateway',
      title: 'AI Shield Gateway',
      role: 'Member 2 (The Shield)',
      tech: 'FastAPI + aiokafka + Redis',
      port: ':8080 (Public)',
      desc: 'Front-line defense. Checks the Redis blocklist, applies sliding-window rate limits, sends eligible requests to the ML engine, and proxies permitted traffic.',
      icon: Shield,
      color: '#0284c7',
    },
    {
      id: 'ml_engine',
      title: 'Neural Engine',
      role: 'Member 1 (The Brain)',
      tech: 'PyTorch Deep Autoencoder + CNN+BiLSTM',
      port: ':8001 (Internal)',
      desc: 'Extracts request features, scores anomalies, and classifies threat categories.',
      icon: Cpu,
      color: '#8b5cf6',
    },
    {
      id: 'redis',
      title: 'Redis In-Memory Store',
      role: 'Shared (M2 & M3)',
      tech: 'Redis 7.2 Alpine',
      port: ':6379',
      desc: 'Holds the dynamic IP blocklist and request rate-limit counters.',
      icon: Server,
      color: '#ef4444',
    },
    {
      id: 'kafka',
      title: 'Kafka Event Bus',
      role: 'Event Streaming',
      tech: 'Confluent Kafka + Zookeeper',
      port: ':9092',
      desc: 'Streams raw request metadata (api.requests.raw) and verdicts (api.verdicts) asynchronously.',
      icon: Network,
      color: '#06b6d4',
    },
    {
      id: 'victim',
      title: 'Victim Backend',
      role: 'Member 3 & 4 (Target)',
      tech: 'FastAPI + PostgreSQL',
      port: ':8081',
      desc: 'Target e-commerce store with SQLi login, stored XSS reviews, and path traversal downloads.',
      icon: Database,
      color: '#10b981',
    },
  ];

  const current = nodes.find((n) => n.id === activeNode) || nodes[1];
  const CurrentIcon = current.icon;

  return (
    <div className="white-card">
      <div className="card-header-row">
        <div>
          <h3 className="card-title">System Architecture Topology</h3>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Microservices Dataflow • Click any subsystem to view details
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {nodes.map((n) => {
          const Icon = n.icon;
          const isSelected = activeNode === n.id;
          return (
            <div
              key={n.id}
              onClick={() => setActiveNode(n.id)}
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                background: isSelected ? 'var(--accent-cyan-light)' : '#f8fafc',
                border: `1px solid ${isSelected ? '#38bdf8' : 'var(--border-light)'}`,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.45rem' }}>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '6px',
                    background: `${n.color}20`,
                    color: n.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Icon size={15} />
                </div>
                <span className="font-mono" style={{ fontSize: '0.72rem', color: n.color, fontWeight: 600 }}>
                  {n.port}
                </span>
              </div>

              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{n.title}</h4>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{n.role}</p>
            </div>
          );
        })}
      </div>

      <div
        style={{
          padding: '1.25rem',
          borderRadius: 'var(--radius-lg)',
          background: '#f8fafc',
          border: '1px solid var(--border-light)',
          display: 'flex',
          gap: '1.25rem',
          alignItems: 'flex-start',
        }}
      >
        <div
          style={{
            width: '44px',
            height: '44px',
            borderRadius: 'var(--radius-md)',
            background: `${current.color}20`,
            color: current.color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <CurrentIcon size={22} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', fontWeight: 600 }}>{current.title}</h3>
            <span className="select-pill font-mono">{current.port}</span>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{current.role}</span>
          </div>

          <div className="font-mono" style={{ fontSize: '0.76rem', color: '#0284c7', marginBottom: '0.35rem' }}>
            Tech: {current.tech}
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>{current.desc}</p>
        </div>
      </div>
    </div>
  );
}
