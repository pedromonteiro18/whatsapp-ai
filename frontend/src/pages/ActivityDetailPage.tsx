import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { ActivityDetail } from '@/components/activities/ActivityDetail';
import { AvailabilityCalendar } from '@/components/activities/AvailabilityCalendar';
import { Loading } from '@/components/Loading';
import { getActivity } from '@/services/activities';
import { createBooking } from '@/services/bookings';
import { useAuth } from '@/contexts/AuthContext';
import type { Activity, TimeSlot } from '@/types/activity';
import type { BookingCreateRequest } from '@/types/booking';
import { AlertCircle, CheckCircle } from 'lucide-react';

export default function ActivityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const [selectedTimeSlot, setSelectedTimeSlot] = useState<TimeSlot | undefined>();
  const [participants, setParticipants] = useState(1);
  const [participantsInput, setParticipantsInput] = useState('1');
  const [specialRequests, setSpecialRequests] = useState('');
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState(false);

  // Fetch activity details
  const {
    data: activity,
    isLoading,
    error,
  } = useQuery<Activity>({
    queryKey: ['activity', id],
    queryFn: async () => {
      try {
        return await getActivity(id!);
      } catch (error) {
        toast.error('Failed to load activity', {
          description: error instanceof Error ? error.message : 'Please try again later',
        });
        throw error;
      }
    },
    enabled: !!id,
  });

  // Create booking mutation
  const createBookingMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: (data) => {
      setBookingSuccess(true);
      setBookingError(null);
      queryClient.invalidateQueries({ queryKey: ['bookings'] });

      // Show success toast
      toast.success('Booking created successfully!', {
        description: `Your ${data.activity.name} booking is pending confirmation`,
      });

      // Redirect to bookings page
      setTimeout(() => {
        navigate('/bookings');
      }, 2000);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.message || 'Failed to create booking';
      setBookingError(message);
      setBookingSuccess(false);

      // Show error toast
      toast.error('Failed to create booking', {
        description: message,
        action: {
          label: 'Try Again',
          onClick: () => {
            setBookingError(null);
          },
        },
      });
    },
  });

  // Reset state when activity changes
  useEffect(() => {
    setParticipants(1);
    setParticipantsInput('1');
    setSelectedTimeSlot(undefined);
  }, [id]);

  // Handle booking submission
  const handleBookNow = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: `/activities/${id}` } });
      return;
    }

    if (!selectedTimeSlot) {
      setBookingError('Please select a time slot');
      return;
    }

    if (participants < 1) {
      setBookingError('Number of participants must be at least 1');
      return;
    }

    if (!activity) {
      setBookingError('Activity information not available');
      return;
    }

    if (participants > activity.capacity_per_slot) {
      setBookingError(`Maximum ${activity.capacity_per_slot} participants allowed`);
      return;
    }

    if (participants > selectedTimeSlot.available_capacity) {
      setBookingError(`Only ${selectedTimeSlot.available_capacity} spots available`);
      return;
    }

    const bookingData: BookingCreateRequest = {
      activity_id: activity.id,
      time_slot_id: selectedTimeSlot.id,
      participants,
      special_requests: specialRequests || undefined,
    };

    createBookingMutation.mutate(bookingData);
  };

  const totalPrice = activity && selectedTimeSlot
    ? (parseFloat(activity.price) * participants).toFixed(2)
    : null;

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Loading size="lg" text="Loading activity details..." centered />
      </div>
    );
  }

  if (error || !activity) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="p-6 text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Activity Not Found</h2>
          <p className="text-muted-foreground mb-4">
            The activity you're looking for doesn't exist or has been removed.
          </p>
          <Button onClick={() => navigate('/activities')}>
            Browse Activities
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-4 max-h-[calc(100vh-5rem)] overflow-hidden">
      <div className="grid grid-cols-2 gap-4 h-full">
        <div className="overflow-y-auto pr-2 max-h-[calc(100vh-6rem)]">
          <ActivityDetail activity={activity} />
        </div>

        <div className="overflow-y-auto pl-2 max-h-[calc(100vh-6rem)]">
          <div className="space-y-2">
          {bookingSuccess && (
            <Card className="p-4 bg-green-50 border-green-200">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-green-900">Booking Created!</h3>
                  <p className="text-sm text-green-700 mt-1">
                    Your booking has been created successfully. Redirecting...
                  </p>
                </div>
              </div>
            </Card>
          )}

          {bookingError && (
            <Card className="p-4 bg-red-50 border-red-200">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-900">Booking Error</h3>
                  <p className="text-sm text-red-700 mt-1">{bookingError}</p>
                </div>
              </div>
            </Card>
          )}

          <Card className="p-2">
            <Label htmlFor="participants" className="text-xs font-semibold mb-1 block">
              Participants
            </Label>
            <Input
              id="participants"
              type="number"
              min={1}
              max={activity.capacity_per_slot}
              value={participantsInput}
              onChange={(e) => {
                const val = e.target.value;
                setParticipantsInput(val);

                // Update actual participants state only if valid
                const numVal = parseInt(val);
                if (!isNaN(numVal) && numVal >= 1 && numVal <= activity.capacity_per_slot) {
                  setParticipants(numVal);
                }
              }}
              onBlur={(e) => {
                const val = e.target.value;
                if (val === '' || parseInt(val) < 1) {
                  setParticipants(1);
                  setParticipantsInput('1');
                } else if (parseInt(val) > activity.capacity_per_slot) {
                  setParticipants(activity.capacity_per_slot);
                  setParticipantsInput(activity.capacity_per_slot.toString());
                }
              }}
              placeholder="Number of people"
              className="h-10 w-48"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Max {activity.capacity_per_slot} per booking
            </p>
          </Card>

          <AvailabilityCalendar
            activityId={activity.id}
            onTimeSlotSelect={setSelectedTimeSlot}
            selectedTimeSlot={selectedTimeSlot}
            participants={participants}
          />

          <Card className="p-2">
            <Label htmlFor="special-requests" className="text-xs font-semibold mb-1 block">
              Special Requests
            </Label>
            <textarea
              id="special-requests"
              value={specialRequests}
              onChange={(e) => setSpecialRequests(e.target.value)}
              placeholder="Any special requirements..."
              className="w-full min-h-[50px] px-2 py-1 text-xs border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </Card>

          <Card className="p-2">
            {totalPrice && (
              <div className="mb-2 pb-2 border-b">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Total:</span>
                  <span className="font-bold text-lg">
                    {activity.currency} ${totalPrice}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {participants} × ${activity.price}
                </p>
              </div>
            )}

            <Button
              onClick={handleBookNow}
              disabled={!selectedTimeSlot || createBookingMutation.isPending}
              className="w-full"
            >
              {createBookingMutation.isPending
                ? 'Processing...'
                : isAuthenticated
                ? 'Book Now'
                : 'Login to Book'}
            </Button>

            {!isAuthenticated && (
              <p className="text-xs text-center text-muted-foreground mt-1">
                You'll be redirected to login
              </p>
            )}
          </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
