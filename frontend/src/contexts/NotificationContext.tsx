import { createContext, useContext, ReactNode } from 'react';
import { toast } from 'sonner';

/**
 * Notification types
 */
type NotificationType = 'success' | 'error' | 'info' | 'warning';

/**
 * Options for notification methods
 */
interface NotificationOptions {
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Notification context interface
 */
interface NotificationContextType {
  showSuccess: (message: string, options?: NotificationOptions) => void;
  showError: (message: string, options?: NotificationOptions) => void;
  showInfo: (message: string, options?: NotificationOptions) => void;
  showWarning: (message: string, options?: NotificationOptions) => void;
}

// Create context with undefined default (will be provided by NotificationProvider)
const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

/**
 * NotificationProvider component
 *
 * Provides a unified notification API using sonner toast library
 *
 * Features:
 * - Consistent API for showing success, error, info, and warning messages
 * - Support for descriptions and action buttons
 * - Customizable duration
 * - Wraps sonner's toast for better consistency
 *
 * Usage:
 * ```tsx
 * <NotificationProvider>
 *   <App />
 * </NotificationProvider>
 * ```
 */
export function NotificationProvider({ children }: { children: ReactNode }) {
  const showSuccess = (message: string, options?: NotificationOptions) => {
    toast.success(message, {
      description: options?.description,
      duration: options?.duration,
      action: options?.action,
    });
  };

  const showError = (message: string, options?: NotificationOptions) => {
    toast.error(message, {
      description: options?.description,
      duration: options?.duration,
      action: options?.action,
    });
  };

  const showInfo = (message: string, options?: NotificationOptions) => {
    toast.info(message, {
      description: options?.description,
      duration: options?.duration,
      action: options?.action,
    });
  };

  const showWarning = (message: string, options?: NotificationOptions) => {
    toast.warning(message, {
      description: options?.description,
      duration: options?.duration,
      action: options?.action,
    });
  };

  const value: NotificationContextType = {
    showSuccess,
    showError,
    showInfo,
    showWarning,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

/**
 * useNotification hook
 *
 * Provides access to notification methods
 *
 * @returns Notification methods (showSuccess, showError, showInfo, showWarning)
 * @throws Error if used outside NotificationProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { showSuccess, showError } = useNotification();
 *
 *   const handleSubmit = async () => {
 *     try {
 *       await submitForm();
 *       showSuccess('Form submitted successfully', {
 *         description: 'Your changes have been saved',
 *       });
 *     } catch (error) {
 *       showError('Failed to submit form', {
 *         description: 'Please try again',
 *         action: {
 *           label: 'Retry',
 *           onClick: handleSubmit,
 *         },
 *       });
 *     }
 *   };
 * }
 * ```
 */
export function useNotification(): NotificationContextType {
  const context = useContext(NotificationContext);

  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }

  return context;
}
