import { useState, useEffect } from 'react';
import { Clock, MapPin, Users, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Booking } from '@/types/booking';
import { formatPrice } from '@/types/activity';
import { BookingActions } from './BookingActions';

interface BookingCardProps {
  booking: Booking;
  onConfirm?: (bookingId: string) => void;
  onCancel?: (bookingId: string, reason?: string) => void;
  isConfirming?: boolean;
  isCancelling?: boolean;
}

/**
 * Get status badge configuration based on booking status
 */
function getStatusConfig(status: Booking['status']) {
  switch (status) {
    case 'pending':
      return {
        label: 'Pending',
        variant: 'default' as const,
        className: 'bg-amber-500 hover:bg-amber-600',
      };
    case 'confirmed':
      return {
        label: 'Confirmed',
        variant: 'default' as const,
        className: 'bg-green-500 hover:bg-green-600',
      };
    case 'cancelled':
      return {
        label: 'Cancelled',
        variant: 'secondary' as const,
        className: 'bg-gray-500 hover:bg-gray-600 text-white',
      };
    case 'completed':
      return {
        label: 'Completed',
        variant: 'secondary' as const,
        className: 'bg-blue-500 hover:bg-blue-600 text-white',
      };
    case 'no_show':
      return {
        label: 'No Show',
        variant: 'destructive' as const,
        className: '',
      };
  }
}

/**
 * Get card border and background styling based on status
 */
function getCardStyling(status: Booking['status']) {
  switch (status) {
    case 'pending':
      return 'border-amber-200 bg-amber-50/30';
    case 'confirmed':
      return 'border-green-200 bg-green-50/30';
    case 'cancelled':
      return 'border-gray-200 bg-gray-50/30';
    case 'completed':
      return 'border-blue-200 bg-blue-50/30';
    case 'no_show':
      return 'border-red-200 bg-red-50/30';
    default:
      return '';
  }
}

/**
 * BookingCard component displays a single booking with status, details, and actions
 *
 * Features:
 * - Status-based color coding (pending, confirmed, cancelled, etc.)
 * - Countdown timer for pending bookings
 * - Activity details (name, time, location, participants)
 * - Conditional action buttons based on status
 * - Responsive layout
 */
export function BookingCard({
  booking,
  onConfirm,
  onCancel,
  isConfirming,
  isCancelling,
}: BookingCardProps) {
  const statusConfig = getStatusConfig(booking.status);
  const cardStyling = getCardStyling(booking.status);

  // Format dates
  const activityDate = format(new Date(booking.time_slot.start_time), 'MMM d, yyyy');
  const activityTime = format(new Date(booking.time_slot.start_time), 'h:mm a');

  // Calculate if booking is in the past
  const isPast = new Date(booking.time_slot.start_time) < new Date();

  // Countdown timer for pending bookings
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [isUrgent, setIsUrgent] = useState(false);

  useEffect(() => {
    if (!booking.expires_at || booking.status !== 'pending') {
      return;
    }

    // Calculate time remaining
    const calculateTimeRemaining = () => {
      const expiresAt = new Date(booking.expires_at!);
      const now = new Date();
      const diffInSeconds = Math.floor((expiresAt.getTime() - now.getTime()) / 1000);

      setTimeRemaining(diffInSeconds);
      setIsUrgent(diffInSeconds > 0 && diffInSeconds < 5 * 60); // Less than 5 minutes
    };

    // Calculate immediately
    calculateTimeRemaining();

    // Update every second
    const interval = setInterval(calculateTimeRemaining, 1000);

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, [booking.expires_at, booking.status]);

  // Format countdown text
  const countdownText = (() => {
    if (!booking.expires_at || booking.status !== 'pending') {
      return null;
    }

    if (timeRemaining === null) {
      return 'Loading...';
    }

    if (timeRemaining <= 0) {
      return 'Expired';
    }

    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;

    if (minutes > 0) {
      return `Expires in ${minutes}m ${seconds}s`;
    }
    return `Expires in ${seconds}s`;
  })();

  return (
    <Card className={`overflow-hidden transition-shadow hover:shadow-lg ${cardStyling}`}>
      {/* Pending booking alert banner */}
      {booking.status === 'pending' && booking.expires_at && (
        <div
          className={`${
            isUrgent ? 'bg-red-500 animate-pulse' : 'bg-amber-500'
          } text-white px-4 py-2 flex items-center gap-2 text-sm`}
        >
          <AlertCircle className="h-4 w-4" />
          <span className="font-medium">{countdownText}</span>
        </div>
      )}

      <CardContent className="p-4 pb-3">
        {/* Header with activity name and status */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <h3 className="text-lg font-semibold line-clamp-2 flex-1">
            {booking.activity.name}
          </h3>
          <Badge variant={statusConfig.variant} className={statusConfig.className}>
            {statusConfig.label}
          </Badge>
        </div>

        {/* Activity details */}
        <div className="space-y-2 text-sm">
          {/* Date and time */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4 flex-shrink-0" />
            <span>
              {activityDate} at {activityTime}
            </span>
          </div>

          {/* Location */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="h-4 w-4 flex-shrink-0" />
            <span className="line-clamp-1">{booking.activity.location}</span>
          </div>

          {/* Participants */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Users className="h-4 w-4 flex-shrink-0" />
            <span>
              {booking.participants} {booking.participants === 1 ? 'person' : 'people'}
            </span>
          </div>
        </div>

        {/* Special requests if present */}
        {booking.special_requests && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium">Special requests:</span> {booking.special_requests}
            </p>
          </div>
        )}

        {/* Action buttons for pending/confirmed bookings */}
        {(booking.status === 'pending' || booking.status === 'confirmed') && (
          <BookingActions
            booking={booking}
            onConfirm={onConfirm!}
            onCancel={onCancel!}
            isConfirming={isConfirming}
            isCancelling={isCancelling}
          />
        )}
      </CardContent>

      {/* Footer with price and metadata */}
      <CardFooter className="p-4 pt-0 flex items-center justify-between text-sm">
        <div>
          <span className="text-lg font-bold">
            {formatPrice(booking.total_price, booking.activity.currency)}
          </span>
          <span className="text-muted-foreground ml-1">total</span>
        </div>

        <div className="text-xs text-muted-foreground">
          {isPast && booking.status === 'confirmed' && 'Past activity'}
          {booking.status === 'cancelled' &&
            booking.cancelled_at &&
            `Cancelled ${format(new Date(booking.cancelled_at), 'MMM d')}`}
          {booking.status === 'confirmed' &&
            !isPast &&
            booking.confirmed_at &&
            `Confirmed ${format(new Date(booking.confirmed_at), 'MMM d')}`}
        </div>
      </CardFooter>
    </Card>
  );
}
