// File: frontend/src/components/common/Button.tsx
// Purpose: Reusable button component with multiple variants
// Features: Loading state, icons, different sizes and colors

import React from 'react';

// Interface extends HTML button attributes to inherit all native button props
// This means our Button accepts onClick, disabled, type, etc. automatically
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;        // Shows spinner instead of text when true
  icon?: React.ReactNode;   // Optional icon component
  children: React.ReactNode; // Button text/content (required)
  darkMode?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',      // Default style
  size = 'medium',          // Default size
  loading = false,          // Not loading by default
  icon,                     // Optional icon
  children,                 // Button content
  className = '',           // Additional CSS classes
  disabled,                 // Inherited from HTMLButtonElement
  darkMode = false,
  ...props                  // Rest of the HTML button props
}) => {
  // Debug: Track button renders and props
  console.log('[Button] Rendering:', { variant, size, loading, disabled });

  // Style mappings for different button variants
  // Each variant has different colors for different purposes
  const variantClasses = {
    primary: darkMode
      ? 'bg-primary hover:bg-primary-dark text-white'
      : 'bg-primary hover:bg-primary-dark text-white',
    secondary: darkMode
      ? 'bg-gray-700 hover:bg-gray-600 text-white'
      : 'bg-gray-600 hover:bg-gray-700 text-white',
    outline: darkMode
      ? 'border-2 border-primary text-primary hover:bg-primary hover:text-white bg-transparent'
      : 'border-2 border-primary text-primary hover:bg-primary hover:text-white',
    danger: darkMode
      ? 'bg-red-700 hover:bg-red-800 text-white'
      : 'bg-red-600 hover:bg-red-700 text-white'
  };

  // Size mappings control padding and text size
  const sizeClasses = {
    small: 'px-3 py-1 text-sm',      // Less padding, smaller text
    medium: 'px-4 py-2',              // Default padding
    large: 'px-6 py-3 text-lg'       // More padding, larger text
  };

  // Combine all classes using template literals
  // The order matters: later classes override earlier ones
  const combinedClasses = `
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    rounded-md 
    font-poppins 
    font-medium
    transition-all 
    duration-200
    flex 
    items-center 
    justify-center 
    space-x-2
    disabled:opacity-50 
    disabled:cursor-not-allowed
    ${className}
  `.trim(); // Remove extra whitespace

  return (
    <button
      className={combinedClasses}
      disabled={disabled || loading}  // Disable during loading
      aria-busy={loading}             // Accessibility: indicate loading state
      {...props}                      // Spread remaining props (onClick, etc.)
    >
      {/* Conditional rendering based on loading state */}
      {loading ? (
        // Show spinner when loading
        <div 
          className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
          aria-label="Loading..."
        />
      ) : (
        // Show icon and text when not loading
        <>
          {icon && <span className="flex-shrink-0">{icon}</span>}
          <span>{children}</span>
        </>
      )}
    </button>
  );
};

// Export for use in other components
export default Button;

// Debug: Confirm component loaded
console.log('[Button] Component loaded successfully');