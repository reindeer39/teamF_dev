import { request } from './client';

export function login(credentials) {
  return request('/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

export function signup(registration) {
  return request('/make_account', {
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
