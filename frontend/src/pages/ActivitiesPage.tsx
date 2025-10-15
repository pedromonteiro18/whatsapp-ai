import { useState, useEffect } from 'react';
import { ActivityFilter } from '@/components/activities/ActivityFilter';
import { ActivityGrid } from '@/components/activities/ActivityGrid';
import { useActivities } from '@/hooks/useActivities';
import type { ActivityFilters } from '@/types/activity';

/**
 * ActivitiesPage - Main page for browsing and filtering activities
 *
 * Features:
 * - Side-by-side filter panel and activity grid
 * - Debounced search input (300ms)
 * - Immediate filter application
 * - Responsive layout (filters collapse on mobile)
 */
export default function ActivitiesPage() {
  const [filters, setFilters] = useState<ActivityFilters>({
    category: 'all',
  });

  // Debounced search to avoid excessive API calls
  const [debouncedFilters, setDebouncedFilters] = useState<ActivityFilters>(filters);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilters(filters);
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [filters]);

  // Fetch activities with debounced filters
  const { data: activities, isLoading, error, refetch } = useActivities(debouncedFilters);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Browse Activities</h1>
        <p className="text-muted-foreground">
          Discover amazing activities and experiences at our resort
        </p>
      </div>

      {/* Main Content */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Filter Sidebar */}
        <aside className="lg:w-64 shrink-0">
          <ActivityFilter filters={filters} onChange={setFilters} />
        </aside>

        {/* Activity Grid */}
        <main className="flex-1">
          <ActivityGrid
            activities={activities || []}
            isLoading={isLoading}
            error={error}
            onRetry={refetch}
          />
        </main>
      </div>
    </div>
  );
}
