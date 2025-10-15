import axios from 'axios';
import type {
  Activity,
  ActivityFilters,
  ActivitiesResponse,
  TimeSlot,
} from '@/types/activity';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Build query params from filters
 */
function buildQueryParams(filters?: ActivityFilters): Record<string, string> {
  if (!filters) return {};

  const params: Record<string, string> = {};

  if (filters.category && filters.category !== 'all') {
    params.category = filters.category;
  }

  if (filters.search) {
    params.search = filters.search;
  }

  if (filters.minPrice !== undefined) {
    params.price_min = filters.minPrice.toString();
  }

  if (filters.maxPrice !== undefined) {
    params.price_max = filters.maxPrice.toString();
  }

  if (filters.ordering) {
    params.ordering = filters.ordering;
  }

  return params;
}

/**
 * Get list of activities with optional filters
 * GET /api/v1/activities/
 */
export async function getActivities(filters?: ActivityFilters): Promise<Activity[]> {
  const params = buildQueryParams(filters);

  const response = await axios.get<ActivitiesResponse>(
    `${API_BASE_URL}/activities/`,
    { params }
  );

  // Return just the results array for simplicity
  // In a real app, you might want to return pagination info too
  return response.data.results || response.data as unknown as Activity[];
}

/**
 * Get a single activity by ID
 * GET /api/v1/activities/:id/
 */
export async function getActivity(id: string): Promise<Activity> {
  const response = await axios.get<Activity>(
    `${API_BASE_URL}/activities/${id}/`
  );
  return response.data;
}

/**
 * Get available time slots for an activity
 * GET /api/v1/activities/:id/availability/
 */
export async function getActivityAvailability(
  id: string,
  params: {
    start_date?: string; // ISO date string
    end_date?: string; // ISO date string
    participants?: number;
  } = {}
): Promise<TimeSlot[]> {
  const response = await axios.get<TimeSlot[]>(
    `${API_BASE_URL}/activities/${id}/availability/`,
    { params }
  );
  return response.data;
}

/**
 * Validate if an activity ID is valid
 */
export function isValidActivityId(id: string): boolean {
  // UUID v4 format
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
}
