import { request } from './client';

export function createInvoice(accountNumber, invoiceAmount, message) {
  return request(`/user/${encodeURIComponent(accountNumber)}/invoice_request`, {
    method: 'POST',
    body: JSON.stringify({
      invoice_amount: invoiceAmount,
      message,
    }),
  });
}

export function getMyInvoices(accountNumber) {
  return request(`/user/${encodeURIComponent(accountNumber)}/invoice_list`);
}

export function getInvoiceInfo(invoiceNumber) {
  return request(`/${encodeURIComponent(invoiceNumber)}/get_inf`);
}

export function payInvoice(invoiceNumber, payload) {
  return request(`/${encodeURIComponent(invoiceNumber)}/pay`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
