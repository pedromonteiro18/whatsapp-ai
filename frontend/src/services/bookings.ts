import apiClient from '@/api/client';
import type {
  Booking,
  BookingCreateRequest,
  BookingCancelRequest,
} from '@/types/booking';

/**
 * Get user's bookings
 * GET /api/v1/bookings/
 * Note: Authorization header is automatically added by the API client interceptor
 */
export async function getBookings(): Promise<Booking[]> {
  const response = await apiClient.get<Booking[]>('/bookings/');
  return response.data;
}

/**
 * Create a new booking
 * POST /api/v1/bookings/
 * Note: Authorization header is automatically added by the API client interceptor
 */
export async function createBooking(data: BookingCreateRequest): Promise<Booking> {
  const response = await apiClient.post<Booking>('/bookings/', data);
  return response.data;
}

/**
 * Confirm a pending booking
 * POST /api/v1/bookings/:id/confirm/
 * Note: Authorization header is automatically added by the API client interceptor
 */
export async function confirmBooking(bookingId: string): Promise<Booking> {
  const response = await apiClient.post<Booking>(
    `/bookings/${bookingId}/confirm/`,
    {}
  );
  return response.data;
}

/**
 * Cancel a booking
 * POST /api/v1/bookings/:id/cancel/
 * Note: Authorization header is automatically added by the API client interceptor
 */
export async function cancelBooking(
  bookingId: string,
  reason?: string
): Promise<Booking> {
  const data: BookingCancelRequest = { booking_id: bookingId, reason };
  const response = await apiClient.post<Booking>(
    `/bookings/${bookingId}/cancel/`,
    data
  );
  return response.data;
}
