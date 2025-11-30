/**
 * Role-based UI utilities
 * OPETSE-5: Role-Based Access Control
 */

export const USER_ROLES = {
  STUDENT: 'student',
  INSTRUCTOR: 'instructor'
};

export const PERMISSIONS = {
  // User management
  CREATE_USER: 'create:user',
  READ_USER: 'read:user',
  UPDATE_USER: 'update:user',
  DELETE_USER: 'delete:user',
  
  // Project management
  CREATE_PROJECT: 'create:project',
  READ_PROJECT: 'read:project',
  UPDATE_PROJECT: 'update:project',
  DELETE_PROJECT: 'delete:project',
  
  // Team management
  CREATE_TEAM: 'create:team',
  READ_TEAM: 'read:team',
  UPDATE_TEAM: 'update:team',
  DELETE_TEAM: 'delete:team',
  
  // Evaluation management
  CREATE_EVALUATION: 'create:evaluation',
  READ_EVALUATION: 'read:evaluation',
  UPDATE_EVALUATION: 'update:evaluation',
  DELETE_EVALUATION: 'delete:evaluation',
  
  // Form management
  CREATE_FORM: 'create:form',
  READ_FORM: 'read:form',
  UPDATE_FORM: 'update:form',
  DELETE_FORM: 'delete:form'
};

// Role-Permission mapping (matches backend)
const ROLE_PERMISSIONS = {
  [USER_ROLES.STUDENT]: [
    PERMISSIONS.READ_USER,
    PERMISSIONS.UPDATE_USER,
    PERMISSIONS.READ_PROJECT,
    PERMISSIONS.READ_TEAM,
    PERMISSIONS.CREATE_EVALUATION,
    PERMISSIONS.READ_EVALUATION,
    PERMISSIONS.READ_FORM
  ],
  [USER_ROLES.INSTRUCTOR]: Object.values(PERMISSIONS) // Instructors have all permissions
};

/**
 * Check if a user role has a specific permission
 * @param {string} role - User role
 * @param {string} permission - Permission to check
 * @returns {boolean} True if role has permission
 */
export const hasPermission = (role, permission) => {
  const permissions = ROLE_PERMISSIONS[role] || [];
  return permissions.includes(permission);
};

/**
 * Get all permissions for a role
 * @param {string} role - User role
 * @returns {string[]} Array of permissions
 */
export const getRolePermissions = (role) => {
  return ROLE_PERMISSIONS[role] || [];
};

/**
 * Check if user is an instructor
 * @param {string} role - User role
 * @returns {boolean} True if instructor
 */
export const isInstructor = (role) => {
  return role === USER_ROLES.INSTRUCTOR;
};

/**
 * Check if user is a student
 * @param {string} role - User role
 * @returns {boolean} True if student
 */
export const isStudent = (role) => {
  return role === USER_ROLES.STUDENT;
};
