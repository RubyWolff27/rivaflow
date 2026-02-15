import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface AdminRouteProps {
  children: React.ReactNode;
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { user } = useAuth();

  if (!user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
