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
  price: string;
  duration: number;
  capacity: number;
  location: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  images: ActivityImage[];
  primary_image?: ActivityImage;
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
  category?: ActivityCategory;
  min_price?: number;
  max_price?: number;
  search?: string;
  ordering?: string;
}
