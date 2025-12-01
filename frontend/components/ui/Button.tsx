import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  className = '',
  disabled = false,
  ...props
}) => {
  const baseStyle =
    'px-6 py-3 rounded-2xl font-bold transition-all transform active:scale-95 flex items-center justify-center gap-2';

  const variants = {
    primary: 'bg-[#1A1A2E] text-white shadow-lg shadow-indigo-200 hover:shadow-indigo-300',
    secondary: 'bg-white text-gray-700 border-2 border-gray-100 hover:bg-gray-50',
    ghost: 'bg-transparent text-gray-500 hover:bg-gray-100',
    danger: 'bg-red-50 text-red-600 hover:bg-red-100',
    success: 'bg-[#CCFF00] text-[#1A1A2E] shadow-lg shadow-lime-200',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyle} ${variants[variant]} ${className} ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      {...props}
    >
      {children}
    </button>
  );
};


