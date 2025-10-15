export interface ActivityImage {
  id: string;
  image: string;
  alt_text: string;
  is_primary: boolean;
  order: number;
}

export interface Activity {
  id: string;
  name: string;
  slug: string;
  description: string;
  category: ActivityCategory;
  price: string; // Decimal as string
  currency: string;
  duration_minutes: number;
  capacity_per_slot: number;
  location: string;
  requirements: string;
  is_active: boolean;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  images: ActivityImage[];
  primary_image: string | null; // URL or null
}

export type ActivityCategory = 'watersports' | 'spa' | 'dining' | 'adventure' | 'wellness';

export interface TimeSlot {
  id: string;
  activity: string;
  start_time: string;
  end_time: string;
  capacity: number;
  booked_count: number;
  is_available: boolean;
  available_capacity: number;
}

export interface ActivityFilters {
  category?: ActivityCategory | 'all';
  search?: string;
  minPrice?: number;
  maxPrice?: number;
  ordering?: string;
}

/**
 * API response for activities list
 */
export interface ActivitiesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Activity[];
}

/**
 * Category display information
 */
export interface CategoryInfo {
  value: ActivityCategory | 'all';
  label: string;
}

/**
 * Category configuration
 */
export const ACTIVITY_CATEGORIES: CategoryInfo[] = [
  { value: 'all', label: 'All Activities' },
  { value: 'watersports', label: 'Water Sports' },
  { value: 'spa', label: 'Spa & Wellness' },
  { value: 'dining', label: 'Dining' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'wellness', label: 'Wellness' },
];

/**
 * Get category label from value
 */
export function getCategoryLabel(category: ActivityCategory | 'all'): string {
  const info = ACTIVITY_CATEGORIES.find(c => c.value === category);
  return info?.label || category;
}

/**
 * Format price for display
 */
export function formatPrice(price: string, currency: string = 'USD'): string {
  const amount = parseFloat(price);
  if (isNaN(amount)) return price;

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
}

/**
 * Format duration for display
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) {
    return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
  }
  return `${hours}h ${remainingMinutes}m`;
}
