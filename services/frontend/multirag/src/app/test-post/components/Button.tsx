import { SpinnerIcon } from './Icons';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'danger';
  isLoading?: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-accent text-white hover:opacity-90 border border-accent/30',
  danger: 'bg-surface-elevated text-foreground-muted border border-border hover:border-red-400 hover:text-red-400 dark:hover:border-red-400 dark:hover:text-red-400',
};

const spinnerStyles = {
  primary: 'text-white',
  danger: 'text-foreground-muted',
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
