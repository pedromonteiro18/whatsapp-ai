import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';
import type { Activity } from '@/types/activity';
import { formatPrice, formatDuration, getCategoryLabel } from '@/types/activity';
import { Clock, MapPin, Users, Info } from 'lucide-react';

interface ActivityDetailProps {
  activity: Activity;
}

export function ActivityDetail({ activity }: ActivityDetailProps) {
  // Sort images by order, with primary image first - memoized to prevent re-render loops
  const sortedImages = useMemo(() => {
    return [...activity.images].sort((a, b) => {
      if (a.is_primary) return -1;
      if (b.is_primary) return 1;
      return a.order - b.order;
    });
  }, [activity.images]);

  // Beautiful gradient placeholder
  const placeholderSvg = useMemo(() =>
    `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='675'%3E%3Cdefs%3E%3ClinearGradient id='grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%2393c5fd;stop-opacity:1' /%3E%3Cstop offset='100%25' style='stop-color:%233b82f6;stop-opacity:1' /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill='url(%23grad)' width='1200' height='675'/%3E%3Cg fill='white' opacity='0.2'%3E%3Ccircle cx='600' cy='270' r='80'/%3E%3Cpath d='M520 350 L560 450 L640 450 L680 350 Z'/%3E%3C/g%3E%3Ctext x='50%25' y='65%25' dominant-baseline='middle' text-anchor='middle' font-family='system-ui,sans-serif' font-size='32' font-weight='600' fill='white' opacity='0.9'%3E${encodeURIComponent(activity.name)}%3C/text%3E%3C/svg%3E`
  , [activity.name]);

  return (
    <div className="space-y-2">
      {/* Image Carousel - Always show with placeholder if no images */}
      <Card className="overflow-hidden">
        <Carousel className="w-full">
          <CarouselContent>
            {sortedImages.length > 0 ? (
              sortedImages.map((image) => (
                <CarouselItem key={image.id}>
                  <div className="h-[28rem] relative bg-muted">
                    <img
                      src={image.image || placeholderSvg}
                      alt={image.alt_text || activity.name}
                      className="w-full h-full object-cover"
                      loading="lazy"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = placeholderSvg;
                      }}
                    />
                  </div>
                </CarouselItem>
              ))
            ) : (
              <CarouselItem>
                <div className="h-[28rem] relative bg-muted">
                  <img
                    src={placeholderSvg}
                    alt={activity.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              </CarouselItem>
            )}
          </CarouselContent>
          {sortedImages.length > 1 && (
            <>
              <CarouselPrevious className="left-4" />
              <CarouselNext className="right-4" />
            </>
          )}
        </Carousel>
      </Card>

      {/* Activity Header */}
      <div>
        <div className="flex items-start justify-between gap-4 mb-1">
          <h1 className="text-2xl font-bold">{activity.name}</h1>
          <Badge variant="secondary" className="text-xs">
            {getCategoryLabel(activity.category)}
          </Badge>
        </div>

        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="text-xl font-bold text-foreground">
            {formatPrice(activity.price, activity.currency)}
          </span>
          <span className="text-xs">per person</span>
        </div>
      </div>

      {/* Quick Info */}
      <Card className="p-2">
        <div className="grid grid-cols-3 gap-2">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <div>
              <div className="text-xs font-medium">Duration</div>
              <div className="text-xs text-muted-foreground">
                {formatDuration(activity.duration_minutes)}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <div>
              <div className="text-xs font-medium">Group Size</div>
              <div className="text-xs text-muted-foreground">
                Up to {activity.capacity_per_slot}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <div>
              <div className="text-xs font-medium">Location</div>
              <div className="text-xs text-muted-foreground truncate">
                {activity.location}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Description */}
      <Card className="p-2">
        <h2 className="text-xs font-semibold mb-1">About This Activity</h2>
        <p className="text-xs text-muted-foreground whitespace-pre-line leading-snug">
          {activity.description}
        </p>
      </Card>

      {/* Requirements */}
      {activity.requirements && (
        <Card className="p-2">
          <div className="flex items-start gap-2">
            <Info className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h2 className="text-xs font-semibold mb-1">
                What You Need to Know
              </h2>
              <p className="text-xs text-muted-foreground whitespace-pre-line leading-snug">
                {activity.requirements}
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
