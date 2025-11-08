import type { Activity, TimeSlot } from './activity';

export type BookingStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show';

export type BookingSource = 'whatsapp' | 'web' | 'admin';

export interface Booking {
  id: string;
  user_phone: string;
  activity: Activity;
  time_slot: TimeSlot;
  status: BookingStatus;
  participants: number;
  special_requests: string;
  total_price: string;
  booking_source: BookingSource;
  created_at: string;
  confirmed_at?: string;
  cancelled_at?: string;
  expires_at?: string;
  metadata: Record<string, unknown>;
}

export interface BookingCreateRequest {
  activity_id: string;
  time_slot_id: string;
  participants: number;
  special_requests?: string;
}

export interface BookingConfirmRequest {
  booking_id: string;
}

export interface BookingCancelRequest {
  booking_id: string;
  reason?: string;
}
