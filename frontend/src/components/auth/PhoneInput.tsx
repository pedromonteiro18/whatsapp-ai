import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { validatePhoneNumber, formatPhoneNumber } from '@/services/auth';

interface PhoneInputProps {
  onSubmit: (phoneNumber: string) => void;
  isLoading?: boolean;
  error?: string;
}

export default function PhoneInput({ onSubmit, isLoading, error }: PhoneInputProps) {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [validationError, setValidationError] = useState<string>('');

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPhoneNumber(value);

    // Clear validation error when user types
    if (validationError) {
      setValidationError('');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate phone number
    const validation = validatePhoneNumber(phoneNumber);
    if (!validation.valid) {
      setValidationError(validation.error || 'Invalid phone number');
      return;
    }

    // Submit the phone number
    onSubmit(phoneNumber);
  };

  const displayError = validationError || error;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="phone">Phone Number</Label>
        <Input
          id="phone"
          type="tel"
          placeholder="+1 234 567 8900"
          value={phoneNumber}
          onChange={handlePhoneChange}
          disabled={isLoading}
          className={displayError ? 'border-destructive' : ''}
          autoComplete="tel"
          autoFocus
        />
        <p className="text-sm text-muted-foreground">
          Enter your phone number in international format (e.g., +1 234 567 8900)
        </p>
        {displayError && (
          <p className="text-sm text-destructive">{displayError}</p>
        )}
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={isLoading || !phoneNumber}
      >
        {isLoading ? 'Sending...' : 'Send Verification Code'}
      </Button>

      {phoneNumber && validatePhoneNumber(phoneNumber).valid && (
        <p className="text-sm text-center text-muted-foreground">
          We'll send a verification code to {formatPhoneNumber(phoneNumber)} via WhatsApp
        </p>
      )}
    </form>
  );
}
