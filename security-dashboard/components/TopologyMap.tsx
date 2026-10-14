'use client';

import React, { useState, useEffect } from 'react';
import { Network, Shield, Cpu, Database, Server, Radio, AlertTriangle } from 'lucide-react';
import { RecentVerdict } from '../lib/types';

export default function TopologyMap({ verdicts }: { verdicts?: RecentVerdict[] }) {
  const [activeNode, setActiveNode] = useState<string>('gateway');
  const [isAttacking, setIsAttacking] = useState(false);
  const [threatDetected, setThreatDetected] = useState(false);
  const [threatVerdict, setThreatVerdict] = useState<RecentVerdict | null>(null);

  const latestVerdict = verdicts && verdicts.length > 0 ? verdicts[0] : null;
  const latestRequestId = latestVerdict?.request_id;

  useEffect(() => {
    if (!latestVerdict || !latestRequestId) return;
    
    // Trigger animation because the ID changed
    setIsAttacking(true);
    if (latestVerdict.action === 'BLOCK' || latestVerdict.action === 'RATE_LIMIT') {
      setThreatDetected(true);
      setThreatVerdict(latestVerdict);
    }
    
    const timer = setTimeout(() => {
      setIsAttacking(false);
    }, 20000); // 20 seconds! Stays on screen for presentation
    
    return () => clearTimeout(timer);
  }, [latestRequestId]); // ONLY re-run when the ID actually changes

  useEffect(() => {
    if (!threatVerdict) return;
    const timer = setTimeout(() => {
      setThreatDetected(false);
      setThreatVerdict(null);
    }, 20000);
    return () => clearTimeout(timer);
  }, [threatVerdict?.request_id]);

  const nodes = [
    { id: 'clients', label: 'External Web', icon: Radio, x: 20, y: 185, color: '#00ff41' },
    { id: 'gateway', label: 'API Shield', icon: Shield, x: 280, y: 185, color: '#00ff41' },
    { id: 'redis', label: 'Redis DB', icon: Server, x: 280, y: 25, color: '#00ff41' },
    { id: 'ml_engine', label: 'ML Brain', icon: Cpu, x: 520, y: 25, color: '#00ff41' },
    { id: 'kafka', label: 'Kafka Bus', icon: Network, x: 380, y: 340, color: '#00ff41' },
    { id: 'backend', label: 'Sec Backend', icon: Database, x: 600, y: 340, color: '#00ff41' },
    { id: 'victim', label: 'Victim App', icon: Database, x: 650, y: 185, color: '#00ff41' }
  ];

  const edges = [
    { from: 'clients', to: 'gateway' },
    { from: 'gateway', to: 'redis' },
    { from: 'gateway', to: 'ml_engine' },
    { from: 'gateway', to: 'kafka' },
    { from: 'kafka', to: 'backend' },
    { from: 'backend', to: 'redis' },
    { from: 'gateway', to: 'victim' },
  ];

  const getPos = (id: string) => nodes.find(n => n.id === id)!;

  const matrixGreen = '#00ff41';
  const alertRed = '#ff003c';
  const textBright = '#e0e0e0';

  return (
    <div style={{ 
      background: 'radial-gradient(circle at center, #0a110a 0%, #000000 100%)', 
      borderRadius: '16px', 
      padding: '1.5rem', 
      border: `1px solid ${isAttacking && threatDetected ? '#550000' : '#003311'}`, 
      boxShadow: isAttacking && threatDetected ? `inset 0 0 50px ${alertRed}30, 0 0 30px ${alertRed}40` : `inset 0 0 30px ${matrixGreen}10, 0 0 25px ${matrixGreen}15`, 
      overflow: 'hidden', 
      position: 'relative',
      transition: 'all 0.5s ease'
    }}>
      <style>{`
        @keyframes flowData {
          from { stroke-dashoffset: 30; }
          to { stroke-dashoffset: 0; }
        }
        @keyframes fillPipe {
          from { stroke-dashoffset: 500; }
          to { stroke-dashoffset: 0; }
        }
        .wire-base {
          stroke: #1a2e1f;
          stroke-width: 3;
          stroke-linecap: round;
        }
        .wire-base-alert {
          stroke: #3a1111;
          stroke-width: 3;
          stroke-linecap: round;
        }
        .data-packet {
          stroke-dasharray: 10 20;
          stroke-linecap: round;
          animation: flowData 1s linear infinite; 
        }
        .data-packet-seq {
          stroke-dasharray: 500;
          stroke-dashoffset: 500;
          animation: fillPipe 2.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        .node-box {
          background: rgba(0, 20, 5, 0.7);
          backdrop-filter: blur(8px);
          border: 1px solid #005511;
          border-radius: 8px;
          padding: 12px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 15px rgba(0, 255, 65, 0.1);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
        }
        .node-box:hover {
          border-color: #00ff41;
          box-shadow: 0 0 20px rgba(0, 255, 65, 0.4), inset 0 0 10px rgba(0, 255, 65, 0.2);
          transform: translateY(-2px);
        }
        .node-box.alert {
          background: rgba(40, 0, 5, 0.8);
          border: 1px solid #ff003c;
          box-shadow: 0 0 30px rgba(255, 0, 60, 0.6), inset 0 0 15px rgba(255, 0, 60, 0.3);
          animation: pulseNode 1.5s infinite alternate; /* Slowed from 0.5s to 1.5s */
        }
        @keyframes pulseNode {
          from { transform: scale(1); box-shadow: 0 0 20px rgba(255, 0, 60, 0.4); }
          to { transform: scale(1.05); box-shadow: 0 0 40px rgba(255, 0, 60, 0.8); }
        }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: '1.5rem', position: 'relative', zIndex: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ color: matrixGreen, fontFamily: 'monospace', fontSize: '1.4rem', textShadow: `0 0 10px ${matrixGreen}`, margin: 0, letterSpacing: '2px' }}>
            [ NEURAL_TOPOLOGY_GRID ]
          </h3>
          <p style={{ color: '#008822', fontFamily: 'monospace', fontSize: '0.85rem', margin: '6px 0 0 0' }}>SYSTEM TRACING ACTIVE // VERDICTS LINKED</p>
        </div>
        
        {/* Dynamic Status Badge */}
        <div style={{ 
          padding: '6px 16px', 
          borderRadius: '20px', 
          background: isAttacking ? (threatDetected ? 'rgba(255,0,60,0.1)' : 'rgba(0,255,65,0.1)') : 'rgba(0,255,65,0.05)',
          border: `1px solid ${isAttacking ? (threatDetected ? alertRed : matrixGreen) : '#005511'}`,
          display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          {isAttacking && threatDetected && <AlertTriangle size={16} color={alertRed} />}
          <span style={{ 
            color: isAttacking ? (threatDetected ? alertRed : matrixGreen) : '#008822', 
            fontFamily: 'monospace', fontSize: '0.8rem', fontWeight: 'bold' 
          }}>
            {isAttacking ? (threatDetected ? 'CRITICAL THREAT BLOCKED' : 'TRAFFIC ANALYSIS') : 'IDLE MONITORING'}
          </span>
        </div>
      </div>

      <div style={{ width: '100%', height: '440px', position: 'relative' }}>
        <svg width="100%" height="100%" viewBox="0 0 800 440" style={{ position: 'absolute', top: 0, left: 0 }}>
          <defs>
            <filter id="glow-green" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="glow-red" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {/* Grid Pattern */}
            <pattern id="matrixGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#00ff41" strokeWidth="0.5" opacity="0.05" />
            </pattern>
          </defs>

          <rect width="100%" height="100%" fill="url(#matrixGrid)" />

          {/* Render Connections */}
          {edges.map((e, i) => {
            const p1 = getPos(e.from);
            const p2 = getPos(e.to);
            const x1 = p1.x + 60; const y1 = p1.y + 45;
            const x2 = p2.x + 60; const y2 = p2.y + 45;

            // State Logic
            const isTargetLine = e.to === 'victim';
            // Now we want the whole path to light up red if there is a threat
            const isAttackPath = true; // Apply to all paths so we can show the forensic trace
            const isBlocked = isTargetLine && threatDetected;

            let wireClass = 'wire-base';
            let packetClass = 'data-packet';
            let packetColor = matrixGreen;
            let packetWidth = 4;
            
            // DEMO SEQUENCE TIMING: Slowed down for explanation
            let animationDelay = '0s';
            if (e.from === 'clients') animationDelay = '0s'; // Hop 1: Into Gateway
            if (e.from === 'gateway' && (e.to === 'ml_engine' || e.to === 'redis')) animationDelay = '2.5s'; // Hop 2: Inspection
            if (e.from === 'gateway' && e.to === 'kafka') animationDelay = '5s'; // Hop 3: Logging
            if (e.from === 'kafka' && e.to === 'backend') animationDelay = '7.5s'; // Hop 4: Async Processing
            if (e.from === 'backend' && e.to === 'redis') animationDelay = '10s'; // Hop 5: Global Blocklist Update
            if (e.from === 'gateway' && e.to === 'victim') animationDelay = '2.5s'; // Hop 2: Passed to target (if allowed)

            if (isBlocked) {
              // Line to target store goes dead
              wireClass = 'wire-base';
              packetClass = '';
              packetColor = 'transparent';
            } else if (isAttacking) {
              wireClass = 'wire-base-alert';
              packetClass = 'data-packet-seq';
              // If it's a blocked threat, color the trace red. If allowed, color it green.
              packetColor = threatDetected ? alertRed : matrixGreen;
              packetWidth = 6;
            } else {
              // Idle background chatter
              packetClass = 'data-packet';
              packetWidth = 2;
              packetColor = '#006611';
            }

            return (
              <g key={`${latestRequestId || 'idle'}-${i}`}>
                {/* Background Solid Wire */}
                <line x1={x1} y1={y1} x2={x2} y2={y2} className={wireClass} style={{ opacity: isBlocked ? 0.3 : 1 }} />
                
                {/* Moving Data Packets over the wire */}
                {packetClass && (
                  <line 
                    x1={x1} y1={y1} x2={x2} y2={y2} 
                    stroke={packetColor} 
                    strokeWidth={packetWidth}
                    className={packetClass} 
                    style={packetClass === 'data-packet-seq' ? { animationDelay } : undefined}
                  />
                )}
              </g>
            )
          })}
          
          {/* Render Nodes */}
          {nodes.map((n) => {
            const Icon = n.icon;
            const isGateway = n.id === 'gateway';
            const isTarget = n.id === 'victim';
            const isAlerting = isAttacking && threatDetected && isGateway;
            
            let iconColor = matrixGreen;
            if (isAlerting) iconColor = '#fff';
            if (isTarget && isAttacking && threatDetected) iconColor = '#444'; // Safe but isolated

            return (
              <foreignObject key={n.id} x={n.x} y={n.y} width="120" height="90" style={{ overflow: 'visible' }}>
                <div 
                  className={`node-box ${isAlerting ? 'alert' : ''}`}
                  onClick={() => setActiveNode(n.id)}
                  style={{ opacity: (isTarget && isAttacking && threatDetected) ? 0.5 : 1 }}
                >
                  <Icon size={30} color={iconColor} style={{ marginBottom: '10px' }} />
                  <span style={{ 
                    color: isAlerting ? '#fff' : textBright, 
                    fontSize: '0.75rem', 
                    fontFamily: 'monospace', 
                    textAlign: 'center', 
                    fontWeight: 700,
                    letterSpacing: '1px'
                  }}>
                    {n.label}
                  </span>
                </div>
              </foreignObject>
            )
          })}
        </svg>
      </div>
      
      {/* HUD Forensic Info Box */}
      {isAttacking && threatDetected && threatVerdict && (
        <div style={{ 
          position: 'absolute', 
          bottom: '2rem', 
          left: '2rem', 
          background: 'rgba(20, 0, 5, 0.85)', 
          backdropFilter: 'blur(10px)',
          border: `1px solid ${alertRed}`, 
          borderLeft: `4px solid ${alertRed}`,
          padding: '1.25rem', 
          borderRadius: '6px', 
          fontFamily: 'monospace', 
          boxShadow: `0 10px 30px rgba(255, 0, 60, 0.4)`,
          minWidth: '280px',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#fff', fontSize: '0.9rem' }}>&gt; FORENSIC_REPORT</h4>
          <div style={{ color: alertRed, fontSize: '0.8rem', lineHeight: '1.5' }}>
            <span style={{color: '#888'}}>IP:</span> {threatVerdict.client_ip}<br/>
            <span style={{color: '#888'}}>THREAT:</span> <span style={{fontWeight: 'bold', color: '#fff'}}>{threatVerdict.threat_type}</span><br/>
            <span style={{color: '#888'}}>SCORE:</span> {threatVerdict.anomaly_score == null ? '—' : threatVerdict.anomaly_score.toFixed(2)}<br/>
            <span style={{color: '#888'}}>ACTION:</span> {threatVerdict.action}<br/>
            <span style={{color: '#888'}}>TARGET:</span> SECURED
          </div>
        </div>
      )}
    </div>
  );
}
