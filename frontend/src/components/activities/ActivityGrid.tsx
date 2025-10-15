import { AlertCircle } from 'lucide-react';
import { ActivityCard } from './ActivityCard';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import type { Activity } from '@/types/activity';

interface ActivityGridProps {
  activities: Activity[];
  isLoading: boolean;
  error: Error | null;
  onRetry?: () => void;
}

/**
 * ActivityGrid component displays activities in a responsive grid
 *
 * Features:
 * - Responsive grid layout (1-3 columns)
 * - Loading state with skeleton cards
 * - Empty state with helpful message
 * - Error state with retry button
 */
export function ActivityGrid({ activities, isLoading, error, onRetry }: ActivityGridProps) {
  // Loading State
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="space-y-4">
            {/* Image skeleton */}
            <Skeleton className="h-48 w-full rounded-lg" />
            {/* Content skeleton */}
            <div className="space-y-2 px-4">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <div className="flex justify-between items-center pt-4">
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-10 w-28" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-semibold mb-2">Failed to Load Activities</h3>
        <p className="text-muted-foreground mb-4 max-w-md">
          {error.message || 'An error occurred while loading activities. Please try again.'}
        </p>
        {onRetry && (
          <Button onClick={onRetry}>
            Try Again
          </Button>
        )}
      </div>
    );
  }

  // Empty State
  if (!activities || activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <div className="rounded-full bg-muted p-6 mb-4">
          <svg
            className="h-12 w-12 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold mb-2">No Activities Found</h3>
        <p className="text-muted-foreground max-w-md">
          We couldn't find any activities matching your criteria. Try adjusting your filters or search terms.
        </p>
      </div>
    );
  }

  // Success State - Display Grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {activities.map((activity) => (
        <ActivityCard key={activity.id} activity={activity} />
      ))}
    </div>
  );
}
