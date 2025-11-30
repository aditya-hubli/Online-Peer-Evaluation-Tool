/**
 * ProtectedRoute component - Wraps content that requires specific permissions
 * OPETSE-5: Role-Based Access Control
 */
import React from 'react';
import { hasPermission, isInstructor, isStudent } from '../lib/rbac';

/**
 * Component that conditionally renders children based on user role/permission
 */
export const ProtectedContent = ({ 
  children, 
  requiredPermission = null,
  requiredRole = null,
  fallback = null,
  userRole = 'student' // Default to student for now (will get from auth context later)
}) => {
  // Check role requirement
  if (requiredRole) {
    if (requiredRole === 'instructor' && !isInstructor(userRole)) {
      return fallback;
    }
    if (requiredRole === 'student' && !isStudent(userRole)) {
      return fallback;
    }
  }
  
  // Check permission requirement
  if (requiredPermission && !hasPermission(userRole, requiredPermission)) {
    return fallback;
  }
  
  return <>{children}</>;
};

/**
 * Component that only renders for instructors
 */
export const InstructorOnly = ({ children, fallback = null }) => {
  return (
    <ProtectedContent requiredRole="instructor" fallback={fallback}>
      {children}
    </ProtectedContent>
  );
};

/**
 * Component that only renders for students
 */
export const StudentOnly = ({ children, fallback = null }) => {
  return (
    <ProtectedContent requiredRole="student" fallback={fallback}>
      {children}
    </ProtectedContent>
  );
};

/**
 * Higher-order component to protect a component with permission check
 */
export const withPermission = (Component, requiredPermission) => {
  return (props) => {
    const userRole = 'student'; // TODO: Get from auth context
    
    if (!hasPermission(userRole, requiredPermission)) {
      return (
        <div className="p-4 text-center">
          <p className="text-red-500">You don't have permission to access this feature.</p>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
};

/**
 * Higher-order component to protect a component with role check
 */
export const withRole = (Component, requiredRole) => {
  return (props) => {
    const userRole = 'student'; // TODO: Get from auth context
    
    if (userRole !== requiredRole) {
      return (
        <div className="p-4 text-center">
          <p className="text-red-500">This feature is only available for {requiredRole}s.</p>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
};
