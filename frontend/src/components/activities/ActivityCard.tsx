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
  const imageUrl = activity.primary_image || activity.images[0]?.image || '/placeholder-activity.jpg';
  const categoryLabel = getCategoryLabel(activity.category);
  const priceDisplay = formatPrice(activity.price, activity.currency);
  const durationDisplay = formatDuration(activity.duration_minutes);

  return (
    <Card className="hover:shadow-lg transition-shadow overflow-hidden">
      {/* Activity Image */}
      <div className="relative h-48 w-full bg-muted overflow-hidden">
        <img
          src={imageUrl}
          alt={activity.name}
          className="h-full w-full object-cover transition-transform hover:scale-105"
          onError={(e) => {
            // Fallback to placeholder if image fails to load
            e.currentTarget.src = '/placeholder-activity.jpg';
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
