import { request } from './client';

export function createTransfer(recipientAccountNumber, transferAmount, message) {
  return request(`/transfers/${encodeURIComponent(recipientAccountNumber)}`, {
    method: 'POST',
    body: JSON.stringify({
      transfer_amount: transferAmount,
      message,
    }),
  });
}
