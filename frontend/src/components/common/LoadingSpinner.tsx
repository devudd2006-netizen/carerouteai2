import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingSpinner({ message, size = 'md' }: LoadingSpinnerProps) {
  const sizeClass = {
    sm: 'w-5 h-5 border-2',
    md: 'w-8 h-8 border-4',
    lg: 'w-12 h-12 border-4',
  }[size];

  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3">
      <div className={`${sizeClass} border-primary-200 border-t-primary-600 rounded-full animate-spin`} />
      {message && <p className="text-gray-500 text-sm animate-pulse">{message}</p>}
    </div>
  );
}
