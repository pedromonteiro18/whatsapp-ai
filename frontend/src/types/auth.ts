export interface OTPRequestRequest {
  phone_number: string;
}

export interface OTPRequestResponse {
  message: string;
  expires_in: number;
}

export interface OTPVerifyRequest {
  phone_number: string;
  otp: string;
}

export interface OTPVerifyResponse {
  session_token: string;
  user_phone: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  userPhone: string | null;
  token: string | null;
}
