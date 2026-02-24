/**
 * Protected Route Component
 *
 * Wraps routes that require authentication.
 * Redirects unauthenticated users to /login.
 * Optionally checks for specific roles.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  /** If specified, only these roles can access the route */
  roles?: string[];
  /** Children to render (if not using Outlet) */
  children?: React.ReactNode;
}

export function ProtectedRoute({ roles, children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, hasRole } = useAuth();
  const location = useLocation();

  // Show loading spinner during initial auth check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Not logged in — redirect to login, saving where they were going
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role check — if roles specified and user doesn't have one
  if (roles && !roles.some(r => hasRole(r))) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-destructive">403</h1>
          <h2 className="text-xl font-semibold">Access Denied</h2>
          <p className="text-muted-foreground">
            You don't have permission to access this page.
            <br />
            Required role: <span className="font-mono">{roles.join(' or ')}</span>
            <br />
            Your role: <span className="font-mono">{user?.role}</span>
          </p>
        </div>
      </div>
    );
  }

  return children ? <>{children}</> : <Outlet />;
}
