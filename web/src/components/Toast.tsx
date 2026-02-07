import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { ToastType } from '../contexts/ToastContext';

interface ToastProps {
  type: ToastType;
  message: string;
  onClose: () => void;
}

export default function Toast({ type, message, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger animation after mount
    setTimeout(() => setIsVisible(true), 10);
  }, []);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300); // Wait for fade-out animation
  };

  const typeConfig = {
    success: {
      icon: CheckCircle,
      bg: 'var(--success-bg)',
      color: 'var(--success)',
      border: 'var(--success)',
    },
    error: {
      icon: XCircle,
      bg: 'var(--danger-bg)',
      color: 'var(--danger)',
      border: 'var(--danger)',
    },
    warning: {
      icon: AlertTriangle,
      bg: 'var(--warning-bg)',
      color: 'var(--warning)',
      border: 'var(--warning)',
    },
    info: {
      icon: Info,
      bg: 'var(--primary-bg)',
      color: 'var(--primary)',
      border: 'var(--primary)',
    },
  };

  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div
      className="rounded-lg shadow-lg border p-4 flex items-start gap-3 transition-all duration-300"
      style={{
        backgroundColor: 'var(--surface)',
        borderColor: config.border,
        transform: isVisible ? 'translateX(0)' : 'translateX(100%)',
        opacity: isVisible ? 1 : 0,
      }}
      role="alert"
      aria-live={type === 'error' ? 'assertive' : 'polite'}
    >
      {/* Icon */}
      <div
        className="p-1.5 rounded-lg flex-shrink-0"
        style={{ backgroundColor: config.bg }}
      >
        <Icon className="w-5 h-5" style={{ color: config.color }} />
      </div>

      {/* Message */}
      <p
        className="flex-1 text-sm leading-relaxed"
        style={{ color: 'var(--text)' }}
      >
        {message}
      </p>

      {/* Close Button */}
      <button
        onClick={handleClose}
        className="p-1 rounded-lg hover:bg-[var(--surfaceElev)] transition-colors flex-shrink-0"
        style={{ color: 'var(--muted)' }}
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
