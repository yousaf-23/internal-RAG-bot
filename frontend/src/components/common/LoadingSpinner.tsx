// File: frontend/src/components/common/LoadingSpinner.tsx
// Purpose: Reusable loading indicator component
// Usage: Shows spinning animation during API calls or data processing

import React from 'react';

// TypeScript Interface: Defines what props this component accepts
// The ? makes properties optional (not required)
interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';  // Size of the spinner
  color?: string;                        // Color (defaults to primary)
  message?: string;                      // Optional text below spinner
  darkMode?: boolean;                   // Dark mode flag
}

// Functional Component using TypeScript
// React.FC = React Functional Component type
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium',        // Default value if not provided
  color = 'primary',      // Default to primary color
  message,                 // No default (optional)
  darkMode = false        // Default to false (light mode)
}) => {
  // Debug: Log when component renders (remove in production)
  console.log('[LoadingSpinner] Rendering with:', { size, color, message, darkMode });

  // Map size prop to Tailwind CSS classes
  // This object acts like a dictionary/lookup table
  const sizeClasses = {
    small: 'w-4 h-4',     // Width: 1rem, Height: 1rem
    medium: 'w-8 h-8',    // Width: 2rem, Height: 2rem  
    large: 'w-12 h-12'    // Width: 3rem, Height: 3rem
  };

  // Render the component UI
  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      {/* Spinner element - CSS animation makes it spin */}
      <div 
        className={`
          ${sizeClasses[size]}  
          animate-spin 
          rounded-full 
          border-2 
          ${darkMode ? 'border-gray-700 border-t-primary' : 'border-gray-300 border-t-primary'}
        `}
        // aria-label helps screen readers understand this is a loading indicator
        aria-label="Loading..."
      />
      
      {/* Conditional rendering: Only show message if it exists */}
      {message && (
        <p className={`text-sm font-poppins animate-pulse ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
          {message}
        </p>
      )}
    </div>
  );
};

// Export so other files can import and use this component
export default LoadingSpinner;

// Debug: Confirm component is loaded (remove in production)
console.log('[LoadingSpinner] Component loaded successfully');