import { request } from './client';


export function createInvoice(invoiceAmount, message) {
  return request('/invoices/', {
    method: 'POST',
    body: JSON.stringify({
      invoice_amount: invoiceAmount,
      message,
    }),
  });
}

export function getMyInvoices() {
  return request('/invoices/');
}

export function getInvoice(invoiceNumber) {
  return request(`/invoices/${encodeURIComponent(invoiceNumber)}/`);
}

export function payInvoice(invoiceNumber) {
  return request(`/invoices/${encodeURIComponent(invoiceNumber)}/pay/`, {
    method: 'POST',
  });
}
