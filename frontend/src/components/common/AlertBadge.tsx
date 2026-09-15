import React from 'react';
import clsx from 'clsx';

interface AlertBadgeProps {
  level: string;
  size?: 'sm' | 'md';
}

export function AlertBadge({ level, size = 'md' }: AlertBadgeProps) {
  const classes = clsx(
    'inline-flex items-center font-medium rounded-full',
    size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
    {
      'bg-green-100 text-green-800': level === 'low',
      'bg-yellow-100 text-yellow-800': level === 'moderate',
      'bg-orange-100 text-orange-800': level === 'high',
      'bg-red-100 text-red-800 animate-pulse': level === 'emergency',
    }
  );

  const labels: Record<string, string> = {
    low: 'Low Risk',
    moderate: 'Moderate',
    high: 'High Risk',
    emergency: '🚨 Emergency',
  };

  return (
    <span className={classes}>
      {labels[level] || level}
    </span>
  );
}
