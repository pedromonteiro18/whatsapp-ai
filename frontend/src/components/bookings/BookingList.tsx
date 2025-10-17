import { Calendar, CheckCircle } from 'lucide-react';
import { BookingCard } from './BookingCard';
import { Skeleton } from '@/components/ui/skeleton';
import type { Booking } from '@/types/booking';

interface BookingListProps {
  bookings?: Booking[];
  isLoading: boolean;
  onConfirm: (bookingId: string) => void;
  onCancel: (bookingId: string, reason?: string) => void;
  isConfirming?: boolean;
  isCancelling?: boolean;
}

/**
 * Group bookings by status for organized display
 */
function groupBookings(bookings: Booking[]) {
  const now = new Date();

  const pending = bookings.filter((b) => b.status === 'pending');

  const confirmed = bookings.filter(
    (b) =>
      b.status === 'confirmed' &&
      new Date(b.time_slot.start_time) >= now
  );

  const past = bookings.filter(
    (b) =>
      (b.status === 'completed' ||
        b.status === 'cancelled' ||
        b.status === 'no_show' ||
        (b.status === 'confirmed' && new Date(b.time_slot.start_time) < now))
  );

  return { pending, confirmed, past };
}

/**
 * Loading skeleton for booking cards
 */
function BookingCardSkeleton() {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex justify-between items-start">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-6 w-20" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      <div className="flex justify-between items-center pt-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  );
}

/**
 * Empty state component
 */
function EmptyState({ icon: Icon, title, description }: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="rounded-full bg-muted p-3 mb-4">
        <Icon className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm">{description}</p>
    </div>
  );
}

/**
 * BookingList component displays bookings grouped by status
 *
 * Features:
 * - Groups bookings into pending, confirmed, and past
 * - Shows pending bookings first (most urgent)
 * - Responsive grid layout
 * - Loading skeletons
 * - Empty states for each group
 */
export function BookingList({
  bookings,
  isLoading,
  onConfirm,
  onCancel,
  isConfirming,
  isCancelling,
}: BookingListProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <BookingCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Empty state - no bookings at all
  if (!bookings || bookings.length === 0) {
    return (
      <EmptyState
        icon={Calendar}
        title="No bookings yet"
        description="You haven't made any bookings yet. Browse our activities to get started!"
      />
    );
  }

  const { pending, confirmed, past } = groupBookings(bookings);

  return (
    <div className="space-y-8">
      {/* Pending Bookings - Most Urgent */}
      {pending.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-1 bg-amber-500 rounded-full" />
            <h2 className="text-2xl font-bold">Pending Confirmation</h2>
            <span className="text-sm text-muted-foreground">
              ({pending.length})
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {pending.map((booking) => (
              <BookingCard
                key={booking.id}
                booking={booking}
                onConfirm={onConfirm}
                onCancel={onCancel}
                isConfirming={isConfirming}
                isCancelling={isCancelling}
              />
            ))}
          </div>
        </section>
      )}

      {/* Confirmed Upcoming Bookings */}
      {confirmed.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-1 bg-green-500 rounded-full" />
            <h2 className="text-2xl font-bold">Upcoming Activities</h2>
            <span className="text-sm text-muted-foreground">
              ({confirmed.length})
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {confirmed.map((booking) => (
              <BookingCard
                key={booking.id}
                booking={booking}
                onConfirm={onConfirm}
                onCancel={onCancel}
                isConfirming={isConfirming}
                isCancelling={isCancelling}
              />
            ))}
          </div>
        </section>
      )}

      {/* Past Bookings */}
      {past.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-1 bg-gray-400 rounded-full" />
            <h2 className="text-2xl font-bold">Past Bookings</h2>
            <span className="text-sm text-muted-foreground">
              ({past.length})
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {past.map((booking) => (
              <BookingCard
                key={booking.id}
                booking={booking}
                onConfirm={onConfirm}
                onCancel={onCancel}
                isConfirming={isConfirming}
                isCancelling={isCancelling}
              />
            ))}
          </div>
        </section>
      )}

      {/* Empty states for specific groups */}
      {pending.length === 0 && confirmed.length === 0 && past.length > 0 && (
        <div className="border-t pt-6">
          <EmptyState
            icon={CheckCircle}
            title="All caught up!"
            description="You have no pending or upcoming bookings. Check out our activities to plan your next adventure!"
          />
        </div>
      )}
    </div>
  );
}
