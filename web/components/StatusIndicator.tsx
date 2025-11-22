'use client';

import { CheckCircle, AlertCircle, XCircle, HelpCircle } from 'lucide-react';

export type StatusType = 'healthy' | 'warning' | 'unhealthy' | 'not_configured' | 'configured' | 'degraded';

interface StatusIndicatorProps {
  status: StatusType;
  message?: string;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig = {
  healthy: {
    color: 'text-green-600',
    bg: 'bg-green-100',
    border: 'border-green-200',
    icon: CheckCircle,
    label: 'Healthy',
  },
  configured: {
    color: 'text-green-600',
    bg: 'bg-green-100',
    border: 'border-green-200',
    icon: CheckCircle,
    label: 'Configured',
  },
  warning: {
    color: 'text-yellow-600',
    bg: 'bg-yellow-100',
    border: 'border-yellow-200',
    icon: AlertCircle,
    label: 'Warning',
  },
  degraded: {
    color: 'text-yellow-600',
    bg: 'bg-yellow-100',
    border: 'border-yellow-200',
    icon: AlertCircle,
    label: 'Degraded',
  },
  unhealthy: {
    color: 'text-red-600',
    bg: 'bg-red-100',
    border: 'border-red-200',
    icon: XCircle,
    label: 'Unhealthy',
  },
  not_configured: {
    color: 'text-gray-600',
    bg: 'bg-gray-100',
    border: 'border-gray-200',
    icon: HelpCircle,
    label: 'Not Configured',
  },
};

export default function StatusIndicator({
  status,
  message,
  showIcon = true,
  size = 'md',
}: StatusIndicatorProps) {
  const config = statusConfig[status] || statusConfig.not_configured;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <div
      className={`
        inline-flex items-center gap-2 rounded-full
        ${config.bg} ${config.color} ${config.border} border
        ${sizeClasses[size]}
      `}
      title={message}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      <span className="font-medium">{config.label}</span>
      {message && size !== 'sm' && (
        <span className="text-xs opacity-75">• {message}</span>
      )}
    </div>
  );
}
