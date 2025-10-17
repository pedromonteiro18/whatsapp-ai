import { useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type { Booking } from '@/types/booking';

interface BookingActionsProps {
  booking: Booking;
  onConfirm: (bookingId: string) => void;
  onCancel: (bookingId: string, reason?: string) => void;
  isConfirming?: boolean;
  isCancelling?: boolean;
}

/**
 * BookingActions component provides confirm and cancel actions for bookings
 *
 * Features:
 * - Confirm button with confirmation dialog for pending bookings
 * - Cancel button with confirmation dialog and optional reason input
 * - Loading states during API operations
 * - Conditional rendering based on booking status
 */
export function BookingActions({
  booking,
  onConfirm,
  onCancel,
  isConfirming = false,
  isCancelling = false,
}: BookingActionsProps) {
  const [cancelReason, setCancelReason] = useState('');
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);

  // Only show actions for pending or confirmed bookings
  const showConfirm = booking.status === 'pending';
  const showCancel = booking.status === 'pending' || booking.status === 'confirmed';

  // Check if booking can be cancelled (not within 24 hours of activity)
  const activityStartTime = new Date(booking.time_slot.start_time);
  const now = new Date();
  const hoursUntilActivity = (activityStartTime.getTime() - now.getTime()) / (1000 * 60 * 60);
  const canCancel = hoursUntilActivity > 24;

  const handleConfirm = () => {
    onConfirm(booking.id);
    setIsConfirmDialogOpen(false);
  };

  const handleCancel = () => {
    onCancel(booking.id, cancelReason || undefined);
    setIsCancelDialogOpen(false);
    setCancelReason('');
  };

  if (!showConfirm && !showCancel) {
    return null;
  }

  return (
    <div className="flex gap-2 mt-3">
      {/* Confirm Button */}
      {showConfirm && (
        <AlertDialog open={isConfirmDialogOpen} onOpenChange={setIsConfirmDialogOpen}>
          <AlertDialogTrigger asChild>
            <Button
              variant="default"
              size="sm"
              className="flex-1 bg-green-600 hover:bg-green-700"
              disabled={isConfirming || isCancelling}
            >
              {isConfirming ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Confirming...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Confirm
                </>
              )}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Booking</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to confirm this booking for{' '}
                <span className="font-semibold">{booking.activity.name}</span>?
                <br />
                <br />
                This will reserve your spot and you'll receive a confirmation via WhatsApp.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isConfirming}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirm}
                disabled={isConfirming}
                className="bg-green-600 hover:bg-green-700"
              >
                {isConfirming ? 'Confirming...' : 'Confirm Booking'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {/* Cancel Button */}
      {showCancel && (
        <AlertDialog open={isCancelDialogOpen} onOpenChange={setIsCancelDialogOpen}>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="flex-1 border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
              disabled={isConfirming || isCancelling || !canCancel}
            >
              {isCancelling ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Cancelling...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-1" />
                  {!canCancel ? 'Too Late to Cancel' : 'Cancel'}
                </>
              )}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Cancel Booking</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to cancel your booking for{' '}
                <span className="font-semibold">{booking.activity.name}</span>?
                <br />
                <br />
                {booking.status === 'confirmed' && (
                  <span className="text-amber-600">
                    Note: Cancellations within 24 hours of the activity are not allowed.
                  </span>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>

            {/* Optional cancellation reason */}
            <div className="space-y-2">
              <Label htmlFor="cancel-reason" className="text-sm">
                Reason for cancellation (optional)
              </Label>
              <Input
                id="cancel-reason"
                placeholder="Let us know why you're cancelling..."
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                disabled={isCancelling}
              />
            </div>

            <AlertDialogFooter>
              <AlertDialogCancel disabled={isCancelling}>Keep Booking</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleCancel}
                disabled={isCancelling}
                className="bg-red-600 hover:bg-red-700"
              >
                {isCancelling ? 'Cancelling...' : 'Cancel Booking'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {/* Show message if can't cancel */}
      {showCancel && !canCancel && (
        <p className="text-xs text-muted-foreground mt-1">
          Cancellations must be made at least 24 hours before the activity
        </p>
      )}
    </div>
  );
}
