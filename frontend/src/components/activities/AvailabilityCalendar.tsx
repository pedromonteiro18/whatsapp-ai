import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { format, addDays, startOfDay, parseISO } from 'date-fns';
import { ChevronDownIcon } from 'lucide-react';
import type { TimeSlot } from '@/types/activity';
import { getActivityAvailability } from '@/services/activities';

interface AvailabilityCalendarProps {
  activityId: string;
  onTimeSlotSelect: (timeSlot: TimeSlot) => void;
  selectedTimeSlot?: TimeSlot;
  participants?: number;
}

export function AvailabilityCalendar({
  activityId,
  onTimeSlotSelect,
  selectedTimeSlot,
  participants = 1,
}: AvailabilityCalendarProps) {
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate date range: today to 14 days from now
  const today = startOfDay(new Date());
  const maxDate = addDays(today, 14);

  // Fetch time slots when date changes
  useEffect(() => {
    if (!selectedDate) return;

    const fetchTimeSlots = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const dateStr = format(selectedDate, 'yyyy-MM-dd');
        const slots = await getActivityAvailability(activityId, {
          start_date: dateStr,
          end_date: dateStr,
          participants,
        });
        setTimeSlots(slots);
      } catch (err) {
        console.error('Error fetching time slots:', err);
        setError('Failed to load available time slots');
        setTimeSlots([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTimeSlots();
  }, [activityId, selectedDate, participants]);

  return (
    <Card className="p-3">
      <h3 className="text-sm font-semibold mb-3">Select Date & Time</h3>

      <div className="flex gap-4">
        {/* Date Picker */}
        <div className="flex flex-col gap-2 flex-1">
          <label className="text-sm font-medium">Date</label>
          <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between font-normal"
              >
                {selectedDate ? format(selectedDate, "MMM d, yyyy") : "Select date"}
                <ChevronDownIcon className="h-4 w-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="p-0" align="start">
              <Calendar
                mode="single"
                selected={selectedDate}
                captionLayout="dropdown"
                onSelect={(date) => {
                  setSelectedDate(date);
                  setDatePickerOpen(false);
                }}
                disabled={(date) => date < today || date > maxDate}
                className="rounded-md shadow-sm w-auto"
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Time Slot Selector */}
        <div className="flex flex-col gap-2 flex-1">
          <label className="text-sm font-medium">Time</label>
          {isLoading ? (
            <Button variant="outline" disabled>
              Loading...
            </Button>
          ) : error ? (
            <Button variant="outline" disabled>
              Error loading times
            </Button>
          ) : timeSlots.length === 0 ? (
            <Button variant="outline" disabled>
              No times available
            </Button>
          ) : (
            <select
              value={selectedTimeSlot?.id || ''}
              onChange={(e) => {
                const slot = timeSlots.find(s => s.id === e.target.value);
                if (slot) onTimeSlotSelect(slot);
              }}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">Select time</option>
              {timeSlots.map((slot) => {
                const canBook = slot.is_available && slot.available_capacity >= participants;
                const startTime = format(parseISO(slot.start_time), 'h:mm a');
                const endTime = format(parseISO(slot.end_time), 'h:mm a');

                return (
                  <option
                    key={slot.id}
                    value={slot.id}
                    disabled={!canBook}
                  >
                    {startTime} - {endTime} ({slot.available_capacity} left)
                  </option>
                );
              })}
            </select>
          )}
        </div>
      </div>
    </Card>
  );
}
