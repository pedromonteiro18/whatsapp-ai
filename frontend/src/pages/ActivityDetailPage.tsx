import { useParams } from 'react-router-dom';

export default function ActivityDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Activity Details</h1>
      <p className="text-muted-foreground">Activity ID: {id}</p>
      <p className="text-muted-foreground mt-2">Activity details coming soon...</p>
    </div>
  );
}
