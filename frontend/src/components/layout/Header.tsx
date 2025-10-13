import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

export default function Header() {
  const { isAuthenticated, userPhone, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold">
          Resort Activities
        </Link>
        <nav className="flex gap-4 items-center">
          <Link to="/activities" className="hover:text-primary">
            Activities
          </Link>
          <Link to="/bookings" className="hover:text-primary">
            My Bookings
          </Link>
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                {userPhone}
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          ) : (
            <Link to="/login">
              <Button variant="default" size="sm">
                Login
              </Button>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
