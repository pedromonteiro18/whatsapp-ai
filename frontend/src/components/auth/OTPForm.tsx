import { useState, useEffect } from 'react';
import { InputOTP, InputOTPGroup, InputOTPSlot } from '@/components/ui/input-otp';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { formatPhoneNumber } from '@/services/auth';

interface OTPFormProps {
  phoneNumber: string;
  onVerify: (otp: string) => void;
  onResend: () => void;
  isLoading?: boolean;
  error?: string;
  expirySeconds?: number; // Default 300 (5 minutes)
}

export default function OTPForm({
  phoneNumber,
  onVerify,
  onResend,
  isLoading,
  error,
  expirySeconds = 300,
}: OTPFormProps) {
  const [otp, setOtp] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(expirySeconds);
  const [canResend, setCanResend] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Countdown timer
  useEffect(() => {
    if (timeRemaining <= 0) {
      setCanResend(true);
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  // Auto-submit when OTP is complete
  useEffect(() => {
    if (otp.length === 6 && !isSubmitting && !isLoading) {
      setIsSubmitting(true);
      onVerify(otp);
      // Reset after a delay to allow for new attempts if verification fails
      setTimeout(() => setIsSubmitting(false), 2000);
    }
  }, [otp, onVerify, isSubmitting, isLoading]);

  const handleResend = () => {
    setOtp('');
    setTimeRemaining(expirySeconds);
    setCanResend(false);
    setIsSubmitting(false);
    onResend();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="text-2xl font-semibold">Enter Verification Code</h2>
        <p className="text-sm text-muted-foreground">
          We sent a 6-digit code to {formatPhoneNumber(phoneNumber)}
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="otp" className="text-center block">
            Verification Code
          </Label>
          <div className="flex justify-center">
            <InputOTP
              maxLength={6}
              value={otp}
              onChange={setOtp}
              disabled={isLoading}
            >
              <InputOTPGroup>
                <InputOTPSlot index={0} />
                <InputOTPSlot index={1} />
                <InputOTPSlot index={2} />
                <InputOTPSlot index={3} />
                <InputOTPSlot index={4} />
                <InputOTPSlot index={5} />
              </InputOTPGroup>
            </InputOTP>
          </div>
          {error && (
            <p className="text-sm text-destructive text-center">{error}</p>
          )}
        </div>

        {/* Timer display */}
        <div className="text-center">
          {!canResend ? (
            <p className="text-sm text-muted-foreground">
              Code expires in{' '}
              <span className="font-semibold text-foreground">
                {formatTime(timeRemaining)}
              </span>
            </p>
          ) : (
            <p className="text-sm text-destructive">
              Code expired. Please request a new one.
            </p>
          )}
        </div>

        {/* Resend button */}
        <div className="text-center">
          {canResend ? (
            <Button
              variant="outline"
              onClick={handleResend}
              disabled={isLoading}
              className="w-full"
            >
              Resend Code
            </Button>
          ) : (
            <Button
              variant="ghost"
              onClick={handleResend}
              disabled={!canResend || isLoading}
              className="text-sm"
            >
              Didn't receive the code? Resend
            </Button>
          )}
        </div>
      </div>

      {isLoading && (
        <p className="text-sm text-center text-muted-foreground">
          Verifying code...
        </p>
      )}
    </div>
  );
}
