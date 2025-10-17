import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getBookings,
  confirmBooking as confirmBookingAPI,
  cancelBooking as cancelBookingAPI,
} from '@/services/bookings';
import type { Booking } from '@/types/booking';

/**
 * React Query hook for managing user bookings
 *
 * Features:
 * - Fetch user's bookings with caching
 * - Confirm pending bookings with optimistic updates
 * - Cancel bookings with optimistic updates
 * - Automatic query invalidation after mutations
 * - Toast notifications for success/error
 *
 * @returns Query and mutation results
 */
export function useBookings() {
  const queryClient = useQueryClient();
  const queryKey = ['bookings'];

  // Query for fetching bookings
  const bookingsQuery = useQuery<Booking[], Error>({
    queryKey,
    queryFn: getBookings,
    // Cache for 2 minutes (bookings change more frequently than activities)
    staleTime: 2 * 60 * 1000,
    // Keep unused data in cache for 5 minutes
    gcTime: 5 * 60 * 1000,
    // Refetch on window focus to catch updates
    refetchOnWindowFocus: true,
    // Retry failed requests 2 times
    retry: 2,
  });

  // Mutation for confirming a booking
  const confirmMutation = useMutation({
    mutationFn: (bookingId: string) => confirmBookingAPI(bookingId),
    // Optimistic update: immediately update UI
    onMutate: async (bookingId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot the previous value
      const previousBookings = queryClient.getQueryData<Booking[]>(queryKey);

      // Optimistically update the booking status
      if (previousBookings) {
        queryClient.setQueryData<Booking[]>(
          queryKey,
          previousBookings.map((booking) =>
            booking.id === bookingId
              ? {
                  ...booking,
                  status: 'confirmed' as const,
                  confirmed_at: new Date().toISOString(),
                }
              : booking
          )
        );
      }

      // Return context for rollback on error
      return { previousBookings };
    },
    // Rollback on error
    onError: (error, _bookingId, context) => {
      if (context?.previousBookings) {
        queryClient.setQueryData(queryKey, context.previousBookings);
      }
      toast.error('Failed to confirm booking', {
        description: error instanceof Error ? error.message : 'Please try again',
      });
    },
    // Refetch to get the latest data from server
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey });
      toast.success('Booking confirmed!', {
        description: `Your ${data.activity.name} booking is confirmed`,
      });
    },
  });

  // Mutation for canceling a booking
  const cancelMutation = useMutation({
    mutationFn: ({ bookingId, reason }: { bookingId: string; reason?: string }) =>
      cancelBookingAPI(bookingId, reason),
    // Optimistic update
    onMutate: async ({ bookingId }) => {
      await queryClient.cancelQueries({ queryKey });

      const previousBookings = queryClient.getQueryData<Booking[]>(queryKey);

      if (previousBookings) {
        queryClient.setQueryData<Booking[]>(
          queryKey,
          previousBookings.map((booking) =>
            booking.id === bookingId
              ? {
                  ...booking,
                  status: 'cancelled' as const,
                  cancelled_at: new Date().toISOString(),
                }
              : booking
          )
        );
      }

      return { previousBookings };
    },
    // Rollback on error
    onError: (error, _variables, context) => {
      if (context?.previousBookings) {
        queryClient.setQueryData(queryKey, context.previousBookings);
      }
      toast.error('Failed to cancel booking', {
        description: error instanceof Error ? error.message : 'Please try again',
      });
    },
    // Refetch after successful cancellation
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey });
      toast.success('Booking cancelled', {
        description: `Your ${data.activity.name} booking has been cancelled`,
      });
    },
  });

  return {
    // Query results
    bookings: bookingsQuery.data,
    isLoading: bookingsQuery.isLoading,
    error: bookingsQuery.error,
    refetch: bookingsQuery.refetch,

    // Mutation functions
    confirmBooking: (bookingId: string) => confirmMutation.mutate(bookingId),
    cancelBooking: (bookingId: string, reason?: string) =>
      cancelMutation.mutate({ bookingId, reason }),

    // Mutation states
    isConfirming: confirmMutation.isPending,
    isCancelling: cancelMutation.isPending,
  };
}

export type UseBookingsReturn = ReturnType<typeof useBookings>;
