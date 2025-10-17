import { Link } from 'react-router-dom';
import { Clock, MapPin } from 'lucide-react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { Activity } from '@/types/activity';
import { formatPrice, formatDuration, getCategoryLabel } from '@/types/activity';

interface ActivityCardProps {
  activity: Activity;
}

/**
 * ActivityCard component displays a single activity in a card format
 *
 * Features:
 * - Shows activity image with fallback
 * - Displays category badge
 * - Shows price, duration, and location
 * - Links to activity detail page
 * - Responsive design (full width on mobile)
 */
export function ActivityCard({ activity }: ActivityCardProps) {
  // Extract image URL from primary_image or first image
  const imageUrl = activity.primary_image || (activity.images.length > 0 ? activity.images[0].image : undefined);

  const categoryLabel = getCategoryLabel(activity.category);
  const priceDisplay = formatPrice(activity.price, activity.currency);
  const durationDisplay = formatDuration(activity.duration_minutes);

  // Beautiful gradient placeholder with icon
  const placeholderSvg = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Cdefs%3E%3ClinearGradient id='grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%2393c5fd;stop-opacity:1' /%3E%3Cstop offset='100%25' style='stop-color:%233b82f6;stop-opacity:1' /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill='url(%23grad)' width='400' height='300'/%3E%3Cg fill='white' opacity='0.3'%3E%3Ccircle cx='200' cy='120' r='40'/%3E%3Cpath d='M160 160 L180 200 L220 200 L240 160 Z'/%3E%3C/g%3E%3Ctext x='50%25' y='75%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui,sans-serif' font-size='16' fill='white' opacity='0.9'%3E${encodeURIComponent(activity.name)}%3C/text%3E%3C/svg%3E`;

  return (
    <Card className="hover:shadow-lg transition-shadow overflow-hidden">
      {/* Activity Image */}
      <div className="relative h-48 w-full bg-muted overflow-hidden">
        <img
          src={imageUrl || placeholderSvg}
          alt={activity.name}
          className="h-full w-full object-cover"
          loading="lazy"
          onError={(e) => {
            // Fallback to inline SVG if image fails to load
            e.currentTarget.src = placeholderSvg;
          }}
        />
        {/* Category Badge */}
        <div className="absolute top-2 right-2">
          <Badge variant="secondary" className="bg-white/90 backdrop-blur-sm">
            {categoryLabel}
          </Badge>
        </div>
      </div>

      {/* Activity Info */}
      <CardContent className="p-4">
        <h3 className="text-lg font-semibold mb-2 line-clamp-1">
          {activity.name}
        </h3>

        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {activity.description}
        </p>

        {/* Meta Info */}
        <div className="flex flex-col gap-2 text-sm">
          <div className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{durationDisplay}</span>
          </div>

          <div className="flex items-center gap-1 text-muted-foreground">
            <MapPin className="h-4 w-4" />
            <span className="line-clamp-1">{activity.location}</span>
          </div>
        </div>
      </CardContent>

      {/* Footer with Price and CTA */}
      <CardFooter className="p-4 pt-0 flex items-center justify-between">
        <div>
          <span className="text-2xl font-bold">{priceDisplay}</span>
          <span className="text-sm text-muted-foreground ml-1">/ person</span>
        </div>

        <Button asChild>
          <Link to={`/activities/${activity.id}`}>
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
