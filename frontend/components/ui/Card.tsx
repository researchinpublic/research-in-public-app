import React from 'react';
import { THEME } from '@/lib/constants/theme';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  animate?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  animate = false,
}) => (
  <div
    className={`bg-white rounded-3xl border border-stone-200 shadow-sm p-6 ${className} ${
      animate ? 'hover:-translate-y-1 transition-transform duration-300' : ''
    }`}
  >
    {children}
  </div>
);


