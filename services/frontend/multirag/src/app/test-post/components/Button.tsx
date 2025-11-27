import { SpinnerIcon } from './Icons';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'success' | 'danger';
  isLoading?: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800',
  success: 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800',
  danger: 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800',
};

export const Button = ({
  variant = 'primary',
  isLoading = false,
  loadingText,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) => {
  return (
    <button
      className={`px-8 py-4 text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed disabled:shadow-none ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <SpinnerIcon className="animate-spin h-5 w-5" />
          {loadingText || 'Loading...'}
        </span>
      ) : (
        children
      )}
    </button>
  );
};
