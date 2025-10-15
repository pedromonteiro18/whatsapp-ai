import { useState } from 'react';
import { Search, X } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { ACTIVITY_CATEGORIES, type ActivityFilters, type ActivityCategory } from '@/types/activity';

interface ActivityFilterProps {
  filters: ActivityFilters;
  onChange: (filters: ActivityFilters) => void;
}

/**
 * ActivityFilter component provides filtering controls for activities
 *
 * Features:
 * - Category selection dropdown
 * - Price range slider (0-500)
 * - Search input with icon
 * - Clear filters button
 * - Immediate filter application (onChange)
 *
 * TODO(human): After implementing, decide on UX pattern:
 * - Should filters apply immediately or require "Apply" button?
 * - Should price values display while dragging slider?
 */
export function ActivityFilter({ filters, onChange }: ActivityFilterProps) {
  // Local state for price range to show while dragging
  const [priceRange, setPriceRange] = useState<[number, number]>([
    filters.minPrice || 0,
    filters.maxPrice || 500
  ]);

  const handleCategoryChange = (value: string) => {
    onChange({
      ...filters,
      category: value as ActivityCategory | 'all',
    });
  };

  const handleSearchChange = (value: string) => {
    onChange({
      ...filters,
      search: value || undefined,
    });
  };

  const handlePriceChange = (values: number[]) => {
    setPriceRange([values[0], values[1]]);
    // Apply filter immediately
    onChange({
      ...filters,
      minPrice: values[0],
      maxPrice: values[1],
    });
  };

  const handleClearFilters = () => {
    setPriceRange([0, 500]);
    onChange({
      category: 'all',
      search: undefined,
      minPrice: undefined,
      maxPrice: undefined,
    });
  };

  const hasActiveFilters =
    filters.category !== 'all' ||
    !!filters.search ||
    filters.minPrice !== undefined ||
    filters.maxPrice !== undefined;

  return (
    <div className="bg-card border rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="h-8 px-2 text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Category Filter */}
      <div className="space-y-2">
        <Label htmlFor="category">Category</Label>
        <Select
          value={filters.category || 'all'}
          onValueChange={handleCategoryChange}
        >
          <SelectTrigger id="category">
            <SelectValue placeholder="Select category" />
          </SelectTrigger>
          <SelectContent>
            {ACTIVITY_CATEGORIES.map((cat) => (
              <SelectItem key={cat.value} value={cat.value}>
                {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Search Filter */}
      <div className="space-y-2">
        <Label htmlFor="search">Search</Label>
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            id="search"
            type="text"
            placeholder="Search activities..."
            value={filters.search || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      {/* Price Range Filter */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Price Range</Label>
          <span className="text-sm text-muted-foreground">
            ${priceRange[0]} - ${priceRange[1]}
          </span>
        </div>
        <Slider
          min={0}
          max={500}
          step={10}
          value={priceRange}
          onValueChange={handlePriceChange}
          className="py-4"
        />
      </div>
    </div>
  );
}
