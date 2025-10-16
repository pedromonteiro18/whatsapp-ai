import axios from 'axios';
import type {
  Booking,
  BookingCreateRequest,
  BookingCancelRequest,
} from '@/types/booking';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Get user's bookings
 * GET /api/v1/bookings/
 */
export async function getBookings(): Promise<Booking[]> {
  const response = await axios.get<Booking[]>(`${API_BASE_URL}/bookings/`);
  return response.data;
}

/**
 * Create a new booking
 * POST /api/v1/bookings/
 */
export async function createBooking(data: BookingCreateRequest): Promise<Booking> {
  const response = await axios.post<Booking>(`${API_BASE_URL}/bookings/`, data);
  return response.data;
}

/**
 * Confirm a pending booking
 * POST /api/v1/bookings/:id/confirm/
 */
export async function confirmBooking(bookingId: string): Promise<Booking> {
  const response = await axios.post<Booking>(
    `${API_BASE_URL}/bookings/${bookingId}/confirm/`
  );
  return response.data;
}

/**
 * Cancel a booking
 * POST /api/v1/bookings/:id/cancel/
 */
export async function cancelBooking(
  bookingId: string,
  reason?: string
): Promise<Booking> {
  const data: BookingCancelRequest = { booking_id: bookingId, reason };
  const response = await axios.post<Booking>(
    `${API_BASE_URL}/bookings/${bookingId}/cancel/`,
    data
  );
  return response.data;
}
