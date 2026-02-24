/**
 * RoleGuard Component
 *
 * Conditionally renders children based on user role.
 * Use this for hiding/showing UI elements (nav items, buttons, etc.)
 */

import { useAuth } from '@/contexts/AuthContext';

interface RoleGuardProps {
  /** Roles allowed to see the children */
  roles: string[];
  /** Content to render if the user has the required role */
  children: React.ReactNode;
  /** Optional fallback if the user doesn't have the role */
  fallback?: React.ReactNode;
}

export function RoleGuard({ roles, children, fallback = null }: RoleGuardProps) {
  const { hasRole } = useAuth();

  if (!roles.some(r => hasRole(r))) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
