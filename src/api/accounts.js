import { request } from './client';

export function getUserSummary(accountNumber) {
  return request(`/user/${encodeURIComponent(accountNumber)}/summary`);
}

export function getRecipientList(accountNumber) {
  return request(`/user/${encodeURIComponent(accountNumber)}/recipient_list`);
}

export function getRecipientInfo(senderAccountNumber, recipientAccountNumber) {
  return request(
    `/user/${encodeURIComponent(senderAccountNumber)}/${encodeURIComponent(recipientAccountNumber)}/recipient`
  );
}
