import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: (userId) => api.get(`/auth/me?user_id=${userId}`),
};

export const usersAPI = {
  list: () => api.get('/users/'),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

export const projectsAPI = {
  list: (params) => api.get('/projects/', { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

export const teamsAPI = {
  list: (params) => api.get('/teams/', { params }),
  get: (id) => api.get(`/teams/${id}`),
  create: (data) => api.post('/teams/', data),
  update: (id, data) => api.put(`/teams/${id}`, data),
  delete: (id) => api.delete(`/teams/${id}`),
  addMember: (teamId, data) => api.post(`/teams/${teamId}/members`, data),
  removeMember: (teamId, userId) => api.delete(`/teams/${teamId}/members/${userId}`),
};

export const formsAPI = {
  list: (params) => api.get('/forms/', { params }),
  get: (id) => api.get(`/forms/${id}`),
  create: (data) => api.post('/forms/', data),
  update: (id, data) => api.put(`/forms/${id}`, data),
  delete: (id) => api.delete(`/forms/${id}`),
  addCriterion: (formId, data) => api.post(`/forms/${formId}/criteria`, data),
  updateCriterion: (formId, criterionId, data) => api.put(`/forms/${formId}/criteria/${criterionId}`, data),
  deleteCriterion: (formId, criterionId) => api.delete(`/forms/${formId}/criteria/${criterionId}`),
  duplicate: (formId, data) => api.post(`/forms/${formId}/duplicate`, data),  // OPETSE-19: Duplicate form
  listVersions: (formId) => api.get(`/forms/${formId}/versions`),  // OPETSE-25: List versions
  getVersion: (formId, versionId) => api.get(`/forms/${formId}/versions/${versionId}`),  // OPETSE-25: Get specific version
  rollback: (formId, versionId) => api.post(`/forms/${formId}/rollback/${versionId}`),  // OPETSE-25: Rollback form
};

export const evaluationsAPI = {
  list: (params) => api.get('/evaluations/', { params }),
  get: (id) => api.get(`/evaluations/${id}`),
  create: (data) => api.post('/evaluations/', data),
  update: (id, data) => api.put(`/evaluations/${id}`, data),
  delete: (id) => api.delete(`/evaluations/${id}`),
  // OPETSE-13: Get student's pending and completed evaluations for dashboard
  getStudentEvaluations: (studentId) => api.get(`/evaluations/student/${studentId}`),
};

export const reportsAPI = {
  project: (id, params) => api.get(`/reports/project/${id}`, { params }),
  team: (id, params) => api.get(`/reports/team/${id}`, { params }),
  user: (id, params) => api.get(`/reports/user/${id}`, { params }),
  form: (id, params) => api.get(`/reports/evaluation-form/${id}`, { params }),
  // OPETSE-32: CSV Export endpoints
  exportProject: (id, params) => api.get(`/reports/project/${id}/export`, { params, responseType: 'blob' }),
  exportTeam: (id, params) => api.get(`/reports/team/${id}/export`, { params, responseType: 'blob' }),
  exportEvaluations: (params) => api.get(`/reports/evaluations/export`, { params, responseType: 'blob' }),
};

// OPETSE-11: Reminder Management API
export const remindersAPI = {
  getUpcomingDeadlines: (hoursAhead = 48) => api.get(`/reminders/upcoming-deadlines?hours_ahead=${hoursAhead}`),
  getStats: (hoursAhead = 48) => api.get(`/reminders/stats?hours_ahead=${hoursAhead}`),
  trigger: (data) => api.post('/reminders/trigger', data),
  sendTestEmail: (email) => api.post(`/reminders/test-email?email=${email}`),
};

// OPETSE-18: Team Chat API
export const chatsAPI = {
  getMessages: (teamId, requesterId, params) => api.get(`/chats/teams/${teamId}/messages?requester_id=${requesterId}`, { params }),
  sendMessage: (teamId, senderId, data) => api.post(`/chats/teams/${teamId}/messages?sender_id=${senderId}`, data),
  deleteMessage: (messageId, requesterId) => api.delete(`/chats/messages/${messageId}?requester_id=${requesterId}`),
  getTeamMembers: (teamId, requesterId) => api.get(`/chats/teams/${teamId}/members?requester_id=${requesterId}`),
};

export default api;
