'use client';

import React from 'react';
import StorefrontPreview from '../../components/StorefrontPreview';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function VictimPage() {
  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: '1rem' }}>
        <Link href="/" className="btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', textDecoration: 'none' }}>
          <ArrowLeft size={14} />
          <span>Back to Security Command Center</span>
        </Link>
      </div>
      <StorefrontPreview />
    </div>
  );
}
