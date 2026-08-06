import { request } from './client';

export function getMySummary() {
  return request('/account/summary');
}

export function getRecipientList() {
  return request('/account/recipients');
}

export function getRecipientInfo(recipientAccountNumber) {
  return request(
    `/account/recipients/${encodeURIComponent(recipientAccountNumber)}`
  );
}
