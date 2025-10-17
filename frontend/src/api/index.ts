/**
 * API Service Layer - Single import point for all API methods
 *
 * Usage:
 *   import { getActivities, createBooking, requestOTP } from '@/api';
 */

// Export the configured axios instance (in case direct access is needed)
export { default as apiClient } from './client';

// Re-export all API methods from service files
export {
  // Activities
  getActivities,
  getActivity,
  getActivityAvailability,
  isValidActivityId,
} from '../services/activities';

export {
  // Authentication
  requestOTP,
  verifyOTP,
  logout,
  getCurrentUser,
  validatePhoneNumber,
  formatPhoneNumber,
} from '../services/auth';

export {
  // Bookings
  getBookings,
  createBooking,
  confirmBooking,
  cancelBooking,
} from '../services/bookings';
