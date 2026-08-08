import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PageSkeleton from './PageSkeleton';

interface PrivateRouteProps {
  children: React.ReactNode;
}

export default function PrivateRoute({ children }: PrivateRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <PageSkeleton />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
