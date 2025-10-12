import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold">
          Resort Activities
        </Link>
        <nav className="flex gap-4">
          <Link to="/activities" className="hover:text-primary">
            Activities
          </Link>
          <Link to="/bookings" className="hover:text-primary">
            My Bookings
          </Link>
          <Link to="/login" className="hover:text-primary">
            Login
          </Link>
        </nav>
      </div>
    </header>
  );
}
