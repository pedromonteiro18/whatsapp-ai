import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { toast } from 'sonner';
import { getActivities } from '@/services/activities';
import type { Activity, ActivityFilters } from '@/types/activity';

/**
 * React Query hook for fetching activities with filters
 *
 * Features:
 * - Automatic caching with stale-while-revalidate
 * - Background refetching
 * - Query invalidation on filter changes
 * - Loading and error states
 * - Toast notifications for errors
 *
 * @param filters Optional filters for activities
 * @returns Query result with activities data
 */
export function useActivities(
  filters?: ActivityFilters
): UseQueryResult<Activity[], Error> {
  // Create a stable query key based on filters
  // This ensures cache is invalidated when filters change
  const queryKey = ['activities', filters];

  const query = useQuery<Activity[], Error>({
    queryKey,
    queryFn: async () => {
      try {
        return await getActivities(filters);
      } catch (error) {
        toast.error('Failed to load activities', {
          description: error instanceof Error ? error.message : 'Please try again later',
        });
        throw error;
      }
    },
    // Cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    // Keep unused data in cache for 10 minutes
    gcTime: 10 * 60 * 1000,
    // Refetch on window focus
    refetchOnWindowFocus: true,
    // Retry failed requests 2 times
    retry: 2,
    // Keep previous data while fetching to prevent flicker
    placeholderData: (previousData) => previousData,
  });

  return query;
}
