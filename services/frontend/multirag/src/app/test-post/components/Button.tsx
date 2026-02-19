import { SpinnerIcon } from './Icons';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'success' | 'danger';
  isLoading?: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-indigo-600 text-white hover:bg-indigo-700 border border-indigo-600',
  success: 'bg-indigo-600 text-white hover:bg-indigo-700 border border-indigo-600',
  danger: 'bg-white text-neutral-700 border border-neutral-300 hover:bg-neutral-50',
};

const spinnerStyles = {
  primary: 'text-white',
  success: 'text-white',
  danger: 'text-neutral-600',
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
      className={`px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <SpinnerIcon className={`animate-spin h-4 w-4 ${spinnerStyles[variant]}`} />
          {loadingText || 'Loading...'}
        </span>
      ) : (
        children
      )}
    </button>
  );
};
