/**
 * useSLATimer Hook
 *
 * Custom hook for managing SLA countdown timer with live updates.
 * Calculates remaining time, percentage used, and urgency level.
 */

import { useState, useEffect, useCallback } from 'react';
import type { SLAInfo } from '../types/nextSteps';

interface SLATimerState {
  remainingHours: number;
  remainingMinutes: number;
  percentageUsed: number;
  isUrgent: boolean;
  isCritical: boolean;
  isExpired: boolean;
  formattedTime: string;
}

export function useSLATimer(sla: SLAInfo, updateIntervalMs: number = 60000) {
  const [timerState, setTimerState] = useState<SLATimerState>(() =>
    calculateTimerState(sla)
  );

  const updateTimer = useCallback(() => {
    setTimerState(calculateTimerState(sla));
  }, [sla]);

  useEffect(() => {
    // Initial calculation
    updateTimer();

    // Set up interval for updates
    const interval = setInterval(updateTimer, updateIntervalMs);

    return () => clearInterval(interval);
  }, [updateTimer, updateIntervalMs]);

  return timerState;
}

function calculateTimerState(sla: SLAInfo): SLATimerState {
  const totalMinutes = sla.sla_hours * 60;
  const elapsedMinutes = sla.elapsed_hours * 60;
  const remainingMinutes = Math.max(0, totalMinutes - elapsedMinutes);

  const remainingHours = Math.floor(remainingMinutes / 60);
  const remainingMins = Math.floor(remainingMinutes % 60);

  const percentageUsed = Math.min(100, (elapsedMinutes / totalMinutes) * 100);

  const isUrgent = percentageUsed >= 70;
  const isCritical = percentageUsed >= 90;
  const isExpired = remainingMinutes <= 0;

  const formattedTime = formatTimeRemaining(remainingHours, remainingMins);

  return {
    remainingHours,
    remainingMinutes: remainingMins,
    percentageUsed,
    isUrgent,
    isCritical,
    isExpired,
    formattedTime,
  };
}

function formatTimeRemaining(hours: number, minutes: number): string {
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return `${days}d ${remainingHours}h`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}
