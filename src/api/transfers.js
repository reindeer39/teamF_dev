import { request } from './client';

export function createTransfer(senderAccountNumber, recipientAccountNumber, transferAmount, message) {
  return request(
    `/user/${encodeURIComponent(senderAccountNumber)}/${encodeURIComponent(recipientAccountNumber)}/transfer`,
    {
      method: 'POST',
      body: JSON.stringify({
        transfer_amount: transferAmount,
        message,
      }),
    }
  );
}
