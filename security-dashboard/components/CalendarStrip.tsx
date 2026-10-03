'use client';

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function CalendarStrip() {
  const [activeDay, setActiveDay] = useState<number>(22);

  const days = [
    { day: 'Sun', date: 19 },
    { day: 'Mon', date: 20 },
    { day: 'Tue', date: 21 },
    { day: 'Wed', date: 22 }, // Active in template
    { day: 'Thu', date: 23 },
    { day: 'Fri', date: 24 },
    { day: 'Sat', date: 25 },
  ];

  return (
    <div className="white-card">
      <div className="calendar-header">
        <button className="calendar-nav-arrow">
          <ChevronLeft size={16} />
        </button>
        <span className="calendar-month">September 2030</span>
        <button className="calendar-nav-arrow">
          <ChevronRight size={16} />
        </button>
      </div>

      <div className="calendar-days-row">
        {days.map((d) => {
          const isActive = d.date === activeDay;
          return (
            <div
              key={d.date}
              className="calendar-day-col"
              style={{ cursor: 'pointer' }}
              onClick={() => setActiveDay(d.date)}
            >
              <span>{d.day}</span>
              <span className={`calendar-day-num ${isActive ? 'active' : ''}`}>
                {d.date}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
