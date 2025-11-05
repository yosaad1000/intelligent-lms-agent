import React, { ReactNode } from 'react';
import { useTheme } from '../../contexts/ThemeContext';

interface ResponsiveWrapperProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  background?: 'transparent' | 'white' | 'gray';
}

const ResponsiveWrapper: React.FC<ResponsiveWrapperProps> = ({
  children,
  className = '',
  maxWidth = 'full',
  padding = 'md',
  background = 'transparent'
}) => {
  const { actualTheme } = useTheme();

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-full'
  };

  const paddingClasses = {
    none: '',
    sm: 'px-2 sm:px-4',
    md: 'px-4 sm:px-6 lg:px-8',
    lg: 'px-6 sm:px-8 lg:px-12'
  };

  const backgroundClasses = {
    transparent: '',
    white: 'bg-white dark:bg-gray-900',
    gray: 'bg-gray-50 dark:bg-gray-800'
  };

  return (
    <div className={`
      w-full mx-auto
      ${maxWidthClasses[maxWidth]}
      ${paddingClasses[padding]}
      ${backgroundClasses[background]}
      ${className}
    `}>
      {children}
    </div>
  );
};

// Mobile-first responsive grid component
interface ResponsiveGridProps {
  children: ReactNode;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  cols = { default: 1, sm: 2, lg: 3 },
  gap = 'md',
  className = ''
}) => {
  const gapClasses = {
    sm: 'gap-3',
    md: 'gap-4 sm:gap-6',
    lg: 'gap-6 sm:gap-8'
  };

  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6'
  };

  const getGridClasses = () => {
    let classes = 'grid';
    
    if (cols.default) classes += ` ${gridCols[cols.default as keyof typeof gridCols]}`;
    if (cols.sm) classes += ` sm:${gridCols[cols.sm as keyof typeof gridCols]}`;
    if (cols.md) classes += ` md:${gridCols[cols.md as keyof typeof gridCols]}`;
    if (cols.lg) classes += ` lg:${gridCols[cols.lg as keyof typeof gridCols]}`;
    if (cols.xl) classes += ` xl:${gridCols[cols.xl as keyof typeof gridCols]}`;
    
    return classes;
  };

  return (
    <div className={`${getGridClasses()} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  );
};

// Mobile-optimized card component
interface MobileCardProps {
  children: ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  border?: boolean;
  hover?: boolean;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  children,
  className = '',
  padding = 'md',
  shadow = 'sm',
  border = true,
  hover = false
}) => {
  const paddingClasses = {
    sm: 'p-3 sm:p-4',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8'
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg'
  };

  return (
    <div className={`
      bg-white dark:bg-gray-800 rounded-lg
      ${paddingClasses[padding]}
      ${shadowClasses[shadow]}
      ${border ? 'border border-gray-200 dark:border-gray-700' : ''}
      ${hover ? 'hover:shadow-md dark:hover:shadow-lg transition-shadow duration-200' : ''}
      ${className}
    `}>
      {children}
    </div>
  );
};

// Mobile-friendly button component
interface MobileButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const MobileButton: React.FC<MobileButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  disabled = false,
  loading = false,
  onClick,
  className = '',
  type = 'button'
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 touch-manipulation';

  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500 disabled:bg-blue-300',
    secondary: 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 focus:ring-gray-500',
    outline: 'border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-gray-500',
    ghost: 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-gray-500'
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',
    md: 'px-4 py-2 text-base min-h-[44px]',
    lg: 'px-6 py-3 text-lg min-h-[52px]'
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? 'w-full' : ''}
        ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
    >
      {loading && (
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent mr-2"></div>
      )}
      {children}
    </button>
  );
};

// Mobile-optimized input component
interface MobileInputProps {
  type?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  error?: string;
  label?: string;
  required?: boolean;
  className?: string;
}

export const MobileInput: React.FC<MobileInputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  error,
  label,
  required = false,
  className = ''
}) => {
  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`
          w-full px-3 py-2 text-base
          border border-gray-300 dark:border-gray-600
          rounded-lg
          bg-white dark:bg-gray-700
          text-gray-900 dark:text-gray-100
          placeholder-gray-500 dark:placeholder-gray-400
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
          min-h-[44px]
          ${error ? 'border-red-500 focus:ring-red-500' : ''}
        `}
      />
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
};

// Responsive navigation component
interface MobileNavProps {
  items: Array<{
    label: string;
    href?: string;
    onClick?: () => void;
    active?: boolean;
    icon?: React.ComponentType<{ className?: string }>;
  }>;
  className?: string;
}

export const MobileNav: React.FC<MobileNavProps> = ({ items, className = '' }) => {
  return (
    <nav className={`flex overflow-x-auto scrollbar-hide ${className}`}>
      <div className="flex space-x-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg min-w-max">
        {items.map((item, index) => (
          <button
            key={index}
            onClick={item.onClick}
            className={`
              flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap
              ${item.active
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700'
              }
            `}
          >
            {item.icon && <item.icon className="h-4 w-4 mr-2" />}
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  );
};

export default ResponsiveWrapper;