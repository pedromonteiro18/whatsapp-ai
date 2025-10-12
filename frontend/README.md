# Resort Activities - Frontend

Modern React frontend for the WhatsApp AI Resort Activities booking system.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query (React Query)** - Server state management
- **Axios** - HTTP client
- **TailwindCSS** - Utility-first CSS framework
- **shadcn/ui** - Accessible component library

## Getting Started

### Prerequisites

- Node.js v18 or higher
- npm v8 or higher

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

### Development

```bash
# Start dev server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/        # Reusable UI components
│   ├── layout/       # Layout components (Header, Footer, Layout)
│   ├── auth/         # Authentication components
│   ├── activities/   # Activity-related components
│   └── bookings/     # Booking-related components
├── pages/            # Route pages
│   ├── LoginPage.tsx
│   ├── ActivitiesPage.tsx
│   ├── ActivityDetailPage.tsx
│   └── BookingsPage.tsx
├── hooks/            # Custom React hooks
├── services/         # API service layer
├── contexts/         # React contexts (Auth, Notifications)
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
└── lib/              # Library utilities (cn helper)
```

## Routes

- `/` - Redirects to `/activities`
- `/login` - Phone authentication with OTP
- `/activities` - Browse all activities
- `/activities/:id` - View activity details and book
- `/bookings` - View and manage user bookings

## Environment Variables

```env
# Backend API URL
VITE_API_URL=http://localhost:8000/api/v1
```

## API Integration

The frontend connects to the Django backend API via:

1. **Development**: Vite proxy forwards `/api` requests to `http://localhost:8000`
2. **Production**: Set `VITE_API_URL` to your deployed backend URL

## Key Features

- **Type Safety**: Full TypeScript coverage with strict mode
- **Path Aliases**: Import with `@/` prefix for cleaner imports
- **Server State**: React Query handles caching, refetching, and synchronization
- **Responsive Design**: Mobile-first approach with Tailwind
- **Accessible Components**: shadcn/ui components follow WCAG guidelines

## Development Tips

### Path Aliases

Use the `@/` alias for cleaner imports:

```typescript
// Instead of: import { cn } from '../../../lib/utils'
import { cn } from '@/lib/utils'
```

### React Query Configuration

Queries are configured with:
- 5-minute stale time
- No refetch on window focus
- 1 retry on failure

### Type Imports

When importing types, use the `type` keyword:

```typescript
import type { Activity } from '@/types/activity'
```

## Next Steps

1. Implement authentication UI (Task 13)
2. Build activity browsing components (Task 14)
3. Create activity detail and booking flow (Task 15)
4. Implement booking management UI (Task 16)
5. Set up API service layer (Task 17)
6. Add error handling and notifications (Task 18)
