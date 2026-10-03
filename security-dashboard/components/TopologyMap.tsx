'use client';

import React, { useState } from 'react';
import { Network, Shield, Cpu, Database, Server, Radio, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function TopologyMap() {
  const [activeNode, setActiveNode] = useState<string>('gateway');

  const nodes = [
    {
      id: 'clients',
      title: 'Clients & Attack Simulator',
      role: 'Member 2 (Simulation)',
      tech: 'Python Script / Kali Linux / Chrome',
      port: 'Dynamic Ingress',
      desc: 'Generates normal e-commerce traffic, SQL injections, XSS payloads, and credential stuffing bursts targeting the store.',
      icon: Radio,
      color: '#f59e0b',
    },
    {
      id: 'gateway',
      title: 'AI Security Shield Gateway',
      role: 'Member 2 (The Shield)',
      tech: 'FastAPI + httpx + aiokafka + Redis',
      port: ':8080 (Public Exposure)',
      desc: 'Single point of entry. Enforces IP blocklists, sliding-window rate limits, intercepts all traffic, queries ML engine in 3.6ms, and proxies allowed requests.',
      icon: Shield,
      color: '#3b82f6',
    },
    {
      id: 'ml_engine',
      title: 'Neural Inference Engine',
      role: 'Member 1 (The Brain)',
      tech: 'PyTorch • Deep Autoencoder • CNN+BiLSTM',
      port: ':8001 (Internal)',
      desc: 'Extracts 18 custom features from URL, headers, and body. Autoencoder checks anomaly score against 0.28 threshold; CNN+BiLSTM classifies threat type with attention weights.',
      icon: Cpu,
      color: '#8b5cf6',
    },
    {
      id: 'redis',
      title: 'Redis In-Memory State Store',
      role: 'Shared (M2 & M3)',
      tech: 'Redis 7.2 Alpine In-Memory',
      port: ':6379',
      desc: 'Stores dynamic IP blocklist with 3600s TTL and atomic sliding-window request counters per IP address for sub-millisecond perimeter protection.',
      icon: Server,
      color: '#ef4444',
    },
    {
      id: 'kafka',
      title: 'Kafka Event Backbone',
      role: 'Shared Infrastructure',
      tech: 'Confluent Kafka + Zookeeper',
      port: ':9092 / :29092',
      desc: 'Asynchronously streams raw requests (api.requests.raw) and gateway decisions (api.verdicts) without blocking client HTTP request pipelining.',
      icon: Network,
      color: '#06b6d4',
    },
    {
      id: 'victim',
      title: 'Victim E-Commerce Backend',
      role: 'Member 3 & 4 (Target)',
      tech: 'FastAPI + asyncpg + PostgreSQL',
      port: ':8081 (Behind Gateway)',
      desc: 'Intentionally vulnerable online store with SQLi login, stored XSS reviews, and path traversal download endpoints for demonstration.',
      icon: Database,
      color: '#10b981',
    },
  ];

  const current = nodes.find((n) => n.id === activeNode) || nodes[1];
  const CurrentIcon = current.icon;

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div className="panel-header" style={{ marginBottom: '1.25rem' }}>
        <div className="panel-title-wrap">
          <Network size={20} color="#06b6d4" />
          <div>
            <h2 className="panel-title" style={{ fontSize: '1.15rem' }}>
              Microservices Defense Pipeline & System Topology
            </h2>
            <span className="panel-subtitle">
              Live architectural dataflow • Click any subsystem to inspect responsibilities & tech stack
            </span>
          </div>
        </div>
      </div>

      {/* Nodes Flow Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        {nodes.map((n) => {
          const Icon = n.icon;
          const isSelected = activeNode === n.id;
          return (
            <div
              key={n.id}
              onClick={() => setActiveNode(n.id)}
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: isSelected ? 'rgba(59, 130, 246, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                border: `1px solid ${isSelected ? n.color : 'var(--border-subtle)'}`,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span
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
                  <Icon size={16} />
                </span>
                <span className="font-mono" style={{ fontSize: '0.72rem', color: n.color }}>
                  {n.port}
                </span>
              </div>

              <h4 style={{ color: '#fff', fontSize: '0.85rem', marginBottom: '2px' }}>{n.title}</h4>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.72rem' }}>{n.role}</p>
            </div>
          );
        })}
      </div>

      {/* Subsystem Detail Card */}
      <div
        style={{
          padding: '1.25rem',
          borderRadius: 'var(--radius-lg)',
          background: '#0a0f1e',
          border: `1px solid ${current.color}40`,
          display: 'flex',
          gap: '1.25rem',
          alignItems: 'flex-start',
        }}
      >
        <div
          style={{
            width: '46px',
            height: '46px',
            borderRadius: 'var(--radius-md)',
            background: `${current.color}20`,
            border: `1px solid ${current.color}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: current.color,
            flexShrink: 0,
          }}
        >
          <CurrentIcon size={24} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
            <h3 style={{ color: '#fff', fontSize: '1.05rem' }}>{current.title}</h3>
            <span
              className="status-pill font-mono"
              style={{ color: current.color, borderColor: `${current.color}40` }}
            >
              PORT: {current.port}
            </span>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{current.role}</span>
          </div>

          <div className="font-mono" style={{ fontSize: '0.76rem', color: '#93c5fd', marginBottom: '0.5rem' }}>
            Tech Stack: {current.tech}
          </div>

          <p style={{ fontSize: '0.78rem', color: '#e2e8f0', lineHeight: 1.5 }}>{current.desc}</p>
        </div>
      </div>
    </div>
  );
}
