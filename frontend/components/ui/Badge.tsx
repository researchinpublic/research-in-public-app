import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  color?: 'pink' | 'blue' | 'green' | 'orange' | 'gray';
}

export const Badge: React.FC<BadgeProps> = ({ children, color = 'gray' }) => {
  const colors = {
    pink: 'bg-pink-100 text-pink-700',
    blue: 'bg-indigo-100 text-indigo-700',
    green: 'bg-lime-100 text-lime-800',
    orange: 'bg-orange-100 text-orange-700',
    gray: 'bg-gray-100 text-gray-700',
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
        colors[color] || colors.gray
      }`}
    >
      {children}
    </span>
  );
};


