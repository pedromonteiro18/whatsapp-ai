import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import PhoneInput from '@/components/auth/PhoneInput';
import OTPForm from '@/components/auth/OTPForm';
import { requestOTP, verifyOTP } from '@/services/auth';

type LoginStep = 'phone' | 'otp';

export default function LoginPage() {
  const [step, setStep] = useState<LoginStep>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/bookings');
    }
  }, [isAuthenticated, navigate]);

  const handlePhoneSubmit = async (phone: string) => {
    setIsLoading(true);
    setError('');

    try {
      await requestOTP(phone);
      setPhoneNumber(phone);
      setStep('otp');
    } catch (err: any) {
      console.error('Error requesting OTP:', err);

      // Handle different error types
      if (err.response?.status === 429) {
        setError('Too many requests. Please try again in 10 minutes.');
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to send verification code. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOTPVerify = async (otp: string) => {
    setIsLoading(true);
    setError('');

    try {
      const response = await verifyOTP(phoneNumber, otp);

      // Login successful
      login(response.session_token, response.user_phone);

      // Redirect to bookings page
      navigate('/bookings');
    } catch (err: any) {
      console.error('Error verifying OTP:', err);

      if (err.response?.status === 401) {
        setError('Invalid or expired code. Please try again.');
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to verify code. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setIsLoading(true);
    setError('');

    try {
      await requestOTP(phoneNumber);
    } catch (err: any) {
      console.error('Error resending OTP:', err);

      if (err.response?.status === 429) {
        setError('Too many requests. Please wait before requesting another code.');
      } else {
        setError('Failed to resend code. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToPhone = () => {
    setStep('phone');
    setPhoneNumber('');
    setError('');
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="w-full max-w-md p-8 space-y-6 bg-card rounded-lg shadow-lg border">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Welcome Back</h1>
          <p className="text-muted-foreground">
            Sign in to manage your activity bookings
          </p>
        </div>

        {step === 'phone' ? (
          <PhoneInput
            onSubmit={handlePhoneSubmit}
            isLoading={isLoading}
            error={error}
          />
        ) : (
          <div className="space-y-4">
            <OTPForm
              phoneNumber={phoneNumber}
              onVerify={handleOTPVerify}
              onResend={handleResendOTP}
              isLoading={isLoading}
              error={error}
            />
            <button
              onClick={handleBackToPhone}
              className="text-sm text-muted-foreground hover:text-foreground w-full text-center"
            >
              ← Change phone number
            </button>
          </div>
        )}

        <div className="pt-4 border-t">
          <p className="text-xs text-center text-muted-foreground">
            By continuing, you agree to receive WhatsApp messages for verification
            and booking notifications.
          </p>
        </div>
      </div>
    </div>
  );
}
