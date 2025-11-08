import { AlertCircle } from 'lucide-react';
import { useBookings } from '@/hooks/useBookings';
import { BookingList } from '@/components/bookings';
import { Loading } from '@/components/Loading';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

export default function BookingsPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const {
    bookings,
    isLoading,
    error,
    refetch,
    confirmBooking,
    cancelBooking,
    isConfirming,
    isCancelling,
  } = useBookings();

  // Wait for auth to load
  if (authLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Loading size="lg" text="Loading..." centered />
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center max-w-md">
            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Authentication Required</h2>
            <p className="text-muted-foreground mb-4">
              Please log in to view your bookings.
            </p>
            <a
              href="/login"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
            >
              Go to Login
            </a>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center max-w-md">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Error Loading Bookings</h2>
            <p className="text-muted-foreground mb-4">
              {error instanceof Error ? error.message : 'Failed to load bookings'}
            </p>
            <Button onClick={() => refetch()}>
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Count pending bookings for header
  const pendingCount = bookings?.filter((b) => b.status === 'pending').length || 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Bookings</h1>
        <p className="text-muted-foreground">
          Manage your resort activity bookings and reservations
        </p>
      </div>

      {/* Pending bookings alert */}
      {pendingCount > 0 && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-900 mb-1">
                Action Required
              </h3>
              <p className="text-sm text-amber-800">
                You have {pendingCount} pending {pendingCount === 1 ? 'booking' : 'bookings'} that
                need confirmation. Please confirm or cancel within the time limit to avoid automatic
                cancellation.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bookings List */}
      <BookingList
        bookings={bookings || []}
        isLoading={isLoading}
        onConfirm={confirmBooking}
        onCancel={cancelBooking}
        isConfirming={isConfirming}
        isCancelling={isCancelling}
      />
    </div>
  );
}
