import { request } from './client';

export function login(credentials) {
  return request('/auth/login/', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

export function signup(registration) {
  return request('/auth/signup/', {
    method: 'POST',
    body: JSON.stringify(registration),
  });
}

export function logout() {
  return request('/auth/logout/', { method: 'POST' });
}

export function getCurrentUser() {
  return request('/auth/me/');
}
