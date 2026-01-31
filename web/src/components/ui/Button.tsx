import { ReactNode, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary';
  className?: string;
}

export function PrimaryButton({ children, className = '', ...props }: Omit<ButtonProps, 'variant'>) {
  return (
    <button className={`btn-primary ${className}`} {...props}>
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = '', ...props }: Omit<ButtonProps, 'variant'>) {
  return (
    <button className={`btn-secondary ${className}`} {...props}>
      {children}
    </button>
  );
}
