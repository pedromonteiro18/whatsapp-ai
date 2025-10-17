import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Loading component size variants
 */
type LoadingSize = 'sm' | 'md' | 'lg';

/**
 * Loading component props
 */
interface LoadingProps {
  /**
   * Size of the loading spinner
   * @default 'md'
   */
  size?: LoadingSize;
  /**
   * Optional text to display below spinner
   */
  text?: string;
  /**
   * Center the loading spinner vertically and horizontally
   * @default false
   */
  centered?: boolean;
  /**
   * Additional CSS classes
   */
  className?: string;
}

/**
 * Size to icon dimension mapping
 */
const sizeMap: Record<LoadingSize, string> = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

/**
 * Size to text size mapping
 */
const textSizeMap: Record<LoadingSize, string> = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

/**
 * Loading component displays a spinning loader with optional text
 *
 * Features:
 * - Three sizes: sm, md, lg
 * - Optional loading text
 * - Centered variant for full-page loading
 * - Accessible with aria-label
 * - Uses lucide-react's Loader2 icon with spin animation
 *
 * @example
 * ```tsx
 * // Simple inline loading
 * <Loading />
 *
 * // Small loading with text
 * <Loading size="sm" text="Loading..." />
 *
 * // Centered full-page loading
 * <Loading size="lg" text="Loading activities..." centered />
 * ```
 */
export function Loading({
  size = 'md',
  text,
  centered = false,
  className,
}: LoadingProps) {
  const iconSize = sizeMap[size];
  const textSize = textSizeMap[size];

  const content = (
    <div
      className={cn(
        'flex flex-col items-center gap-2',
        centered && 'justify-center min-h-[200px]',
        className
      )}
      role="status"
      aria-label={text || 'Loading'}
    >
      {/* Spinning loader icon */}
      <Loader2 className={cn(iconSize, 'animate-spin text-primary')} />

      {/* Optional loading text */}
      {text && (
        <p className={cn(textSize, 'text-muted-foreground')}>
          {text}
        </p>
      )}

      {/* Screen reader only text */}
      <span className="sr-only">Loading...</span>
    </div>
  );

  // If centered, wrap in a full-height container
  if (centered) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        {content}
      </div>
    );
  }

  return content;
}
