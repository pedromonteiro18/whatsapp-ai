import axios from 'axios';
import type {
  OTPRequestRequest,
  OTPRequestResponse,
  OTPVerifyRequest,
  OTPVerifyResponse
} from '@/types/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Request OTP for phone number verification
 * POST /api/v1/auth/request-otp/
 */
export async function requestOTP(phoneNumber: string): Promise<OTPRequestResponse> {
  const response = await axios.post<OTPRequestResponse>(
    `${API_BASE_URL}/auth/request-otp/`,
    { phone_number: phoneNumber } as OTPRequestRequest
  );
  return response.data;
}

/**
 * Verify OTP and get session token
 * POST /api/v1/auth/verify-otp/
 */
export async function verifyOTP(
  phoneNumber: string,
  otp: string
): Promise<OTPVerifyResponse> {
  const response = await axios.post<OTPVerifyResponse>(
    `${API_BASE_URL}/auth/verify-otp/`,
    { phone_number: phoneNumber, otp } as OTPVerifyRequest
  );
  return response.data;
}

/**
 * Logout and delete session
 * POST /api/v1/auth/logout/
 */
export async function logout(token: string): Promise<void> {
  await axios.post(
    `${API_BASE_URL}/auth/logout/`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
}

/**
 * Get current user information
 * GET /api/v1/auth/me/
 */
export async function getCurrentUser(token: string): Promise<{ phone_number: string; authenticated: boolean }> {
  const response = await axios.get(
    `${API_BASE_URL}/auth/me/`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
}

/**
 * Validate phone number format (E.164)
 * Should start with + and contain 10-15 digits
 */
export function validatePhoneNumber(phoneNumber: string): { valid: boolean; error?: string } {
  // Remove all whitespace and dashes for validation
  const cleaned = phoneNumber.replace(/[\s-]/g, '');

  // Check if it starts with +
  if (!cleaned.startsWith('+')) {
    return { valid: false, error: 'Phone number must start with +' };
  }

  // Check if it contains only + and digits
  if (!/^\+\d+$/.test(cleaned)) {
    return { valid: false, error: 'Phone number can only contain + and digits' };
  }

  // Check length (1-3 digit country code + 10-12 digit number)
  const digits = cleaned.slice(1); // Remove +
  if (digits.length < 10 || digits.length > 15) {
    return { valid: false, error: 'Phone number must be 10-15 digits' };
  }

  return { valid: true };
}

/**
 * Format phone number for display
 * +1234567890 -> +1 234 567 890
 */
export function formatPhoneNumber(phoneNumber: string): string {
  const cleaned = phoneNumber.replace(/[\s-]/g, '');
  if (!cleaned.startsWith('+')) {
    return phoneNumber;
  }

  const countryCode = cleaned.slice(0, 2); // +1
  const rest = cleaned.slice(2);

  // Group remaining digits in chunks of 3
  const chunks = rest.match(/.{1,3}/g) || [];
  return `${countryCode} ${chunks.join(' ')}`;
}
