import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProcessPayment from './ProcessPayment';
import { getUserSummary } from '../api/accounts';
import { getInvoiceInfo, payInvoice } from '../api/invoices';


jest.mock('../api/accounts');
jest.mock('../api/invoices');

const invoiceNumber = '33333333-3333-4333-8333-333333333333';
const myAccountNumber = '1000002';

beforeEach(() => {
  jest.clearAllMocks();
  getInvoiceInfo.mockResolvedValue({
    invoice_account_number: '1000001',
    invoice_amount: '2500',
    invoice_message: '夕食代',
    invoice_flag: 'notpay',
  });
  getUserSummary.mockImplementation((accountNumber) => {
    if (accountNumber === '1000001') {
      return Promise.resolve({
        account_number: '1000001',
        user_name: '請求者',
        user_icon: 'avatar-01.png',
        account_balance: 50000,
      });
    }
    return Promise.resolve({
      account_number: myAccountNumber,
      user_name: '支払者',
      account_balance: 10000,
    });
  });
  payInvoice.mockResolvedValue({
    payment_amount: 2500,
    transaction_number: '11111111-1111-4111-8111-111111111111',
    payer_account_balance: 7500,
  });
});

function renderPayment(props = {}) {
  return render(
    <MemoryRouter
      initialEntries={[`/invoice/${invoiceNumber}`]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <ProcessPayment
        invoiceNumber={invoiceNumber}
        myAccountNumber={myAccountNumber}
        {...props}
      />
    </MemoryRouter>
  );
}

test('URLの請求番号からDBの請求内容とログイン口座残高を表示する', async () => {
  renderPayment();

  expect(await screen.findByText('請求者')).toBeInTheDocument();
  expect(screen.getByText('10,000円')).toBeInTheDocument();
  expect(screen.getByText('2,500円')).toBeInTheDocument();
  expect(screen.getByText('夕食代')).toBeInTheDocument();
  expect(screen.getByAltText('請求者のアイコン').getAttribute('src')).toContain(
    'avatar-01'
  );
  expect(getInvoiceInfo).toHaveBeenCalledWith(invoiceNumber);
  expect(getUserSummary).toHaveBeenCalledWith(myAccountNumber);
  expect(getUserSummary).toHaveBeenCalledWith('1000001');
});

test('請求元本人には別アカウントへ切り替える導線を表示する', async () => {
  getUserSummary.mockImplementation(() =>
    Promise.resolve({
      account_number: '1000001',
      user_name: '請求者',
      account_balance: 10000,
    })
  );
  const onSwitchAccount = jest.fn().mockResolvedValue();
  renderPayment({ myAccountNumber: '1000001', onSwitchAccount });

  expect(
    await screen.findByText(/支払者のアカウントへ切り替えてください/)
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '別のアカウントでログイン' }));

  await waitFor(() => expect(onSwitchAccount).toHaveBeenCalledTimes(1));
});

test('支払うボタンで請求支払いAPIを呼び完了結果を表示する', async () => {
  renderPayment();
  const payButton = await screen.findByRole('button', { name: '支払う' });
  await waitFor(() => expect(payButton).toBeEnabled());
  fireEvent.click(payButton);

  await waitFor(() =>
    expect(payInvoice).toHaveBeenCalledWith(invoiceNumber, {
      my_account_number: myAccountNumber,
      invoice_account_number: '1000001',
      invoice_amount: 2500,
      message: '夕食代',
    })
  );
  expect(await screen.findByText('支払いが完了しました')).toBeInTheDocument();
  expect(screen.getByText(/11111111-1111-4111-8111-111111111111/)).toBeInTheDocument();
});

test('支払い完了後にトップへ戻ると更新後の残高を通知する', async () => {
  const onPaymentComplete = jest.fn();
  renderPayment({ onPaymentComplete });

  const payButton = await screen.findByRole('button', { name: '支払う' });
  await waitFor(() => expect(payButton).toBeEnabled());
  fireEvent.click(payButton);
  fireEvent.click(await screen.findByRole('button', { name: 'トップへ戻る' }));

  expect(onPaymentComplete).toHaveBeenCalledWith(
    expect.objectContaining({ payer_account_balance: 7500 })
  );
});
