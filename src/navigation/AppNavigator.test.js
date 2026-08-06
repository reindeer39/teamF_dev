import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AppNavigator from './AppNavigator';
import { getMySummary, getRecipientInfo, getRecipientList } from '../api/accounts';
import { createTransfer } from '../api/transfers';
import { createInvoice, getInvoice, getMyInvoices } from '../api/invoices';
import { useAuth } from '../auth/AuthContext';

jest.mock('../api/accounts');
jest.mock('../api/transfers');
jest.mock('../api/invoices');
jest.mock('../auth/AuthContext');

const summary = {
  account_number: '1000001',
  user_icon: '/icons/user1.png',
  user_name: '山田太郎',
  account_balance: 97000,
};
const signOut = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  useAuth.mockReturnValue({
    session: { email: 'yamada@example.com', account: summary },
    initializing: false,
    login: jest.fn(),
    signup: jest.fn(),
    signOut,
  });
  getMySummary.mockResolvedValue(summary);
  getRecipientList.mockResolvedValue({
    recipient_list: [
      {
        account_number: '1000002',
        user_icon: '/icons/user2.png',
        user_name: '佐藤花子',
      },
    ],
  });
  getRecipientInfo.mockResolvedValue({
    sender_account_number: '1000001',
    sender_account_balance: 97000,
    recipient_account_number: '1000002',
    recipient_icon: '/icons/user2.png',
    recipient_name: '佐藤花子',
  });
  createTransfer.mockResolvedValue({
    transaction_number: '33333333-3333-4333-8333-333333333333',
    sender_account_number: '1000001',
    recipient_account_number: '1000002',
    transfer_amount: 3000,
    message: '昼食代',
    sender_account_balance: 94000,
  });
  createInvoice.mockResolvedValue({
    invoice_number: '33333333-3333-4333-8333-333333333333',
    invoice_link: 'http://localhost:3000/invoice/33333333-3333-4333-8333-333333333333',
  });
  getMyInvoices.mockResolvedValue({ invoice_list: [] });
  getInvoice.mockResolvedValue({
    invoice_number: '33333333-3333-4333-8333-333333333333',
    invoice_amount: 2500,
    message: '夕食代',
    invoice_flag: 'notpay',
    issuer: {
      account_number: '1000001',
      user_name: '山田太郎',
      user_icon: '/icons/user1.png',
    },
  });
});

function renderNavigator(initialEntries = ['/']) {
  return render(
    <MemoryRouter
      initialEntries={initialEntries}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <AppNavigator />
    </MemoryRouter>
  );
}

test('DBから取得した口座情報と操作ボタンを表示する', async () => {
  renderNavigator();

  expect(await screen.findByText('山田太郎')).toBeInTheDocument();
  expect(screen.getByText('97,000円')).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByRole('button', { name: '送金する' })).toBeEnabled();
  });
  expect(screen.getByRole('button', { name: '請求する' })).toBeInTheDocument();
  expect(getMySummary).toHaveBeenCalledWith();
});

test('請求するボタンから請求リンク作成画面へ遷移し、戻ることができる', async () => {
  renderNavigator();

  fireEvent.click(await screen.findByRole('button', { name: '請求する' }));

  expect(screen.getByLabelText('請求金額')).toBeInTheDocument();
  expect(screen.getByLabelText('メッセージ（任意）')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'リンク作成' })).toBeDisabled();

  fireEvent.click(screen.getByRole('button', { name: '戻る' }));
  expect(await screen.findByRole('button', { name: '請求する' })).toBeInTheDocument();
});

test('請求リンク作成APIのUUIDリンクをコピー画面へ表示する', async () => {
  renderNavigator();
  fireEvent.click(await screen.findByRole('button', { name: '請求する' }));
  fireEvent.change(screen.getByLabelText('請求金額'), {
    target: { value: '2500' },
  });
  fireEvent.change(screen.getByLabelText('メッセージ（任意）'), {
    target: { value: '夕食代' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'リンク作成' }));

  await waitFor(() => expect(createInvoice).toHaveBeenCalledWith(2500, '夕食代'));
  expect(
    await screen.findByText(
      'http://localhost:3000/invoice/33333333-3333-4333-8333-333333333333'
    )
  ).toBeInTheDocument();
});

test('コピー画面からログアウトして同じ請求URLを別アカウントで開ける', async () => {
  renderNavigator();
  fireEvent.click(await screen.findByRole('button', { name: '請求する' }));
  fireEvent.change(screen.getByLabelText('請求金額'), {
    target: { value: '2500' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'リンク作成' }));
  fireEvent.click(
    await screen.findByRole('button', { name: '別のアカウントで支払いを確認' })
  );

  await waitFor(() => expect(signOut).toHaveBeenCalledTimes(1));
  await waitFor(() => expect(getInvoice).toHaveBeenCalledWith(
    '33333333-3333-4333-8333-333333333333'
  ));
});

test('請求状態確認画面がDB取得APIを呼ぶ', async () => {
  renderNavigator();
  fireEvent.click(await screen.findByRole('button', { name: '請求状態確認' }));

  expect(screen.getByText('お願いした請求')).toBeInTheDocument();
  expect(screen.getByText(/請求元：/)).toBeInTheDocument();
  expect(screen.getByText('山田太郎', { selector: 'strong' })).toBeInTheDocument();
  expect(await screen.findByText('請求はありません。')).toBeInTheDocument();
  expect(getMyInvoices).toHaveBeenCalledTimes(1);
});

test('請求元の確認画面へ支払状態と支払者アイコンを反映し再取得できる', async () => {
  getMyInvoices.mockResolvedValue({
    invoice_list: [
      {
        invoice_number: '44444444-4444-4444-8444-444444444444',
        invoice_time: '2026-08-06 02:23:25.573786',
        invoice_amount: 3000,
        message: '昼食代',
        invoice_flag: 'paid',
        paid_by: {
          account_number: '1000002',
          user_name: '佐藤花子',
          user_icon: '/icons/user2.png',
          account_balance: 50000,
        },
      },
    ],
  });
  renderNavigator();
  fireEvent.click(await screen.findByRole('button', { name: '請求状態確認' }));

  expect(await screen.findByText('支払済み')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /請求詳細を開く/ }));
  expect(screen.getByText('佐藤花子')).toBeInTheDocument();
  expect(screen.getByAltText('佐藤花子のアイコン').getAttribute('src')).toContain(
    'human2'
  );

  fireEvent.click(screen.getByRole('button', { name: '最新の状態に更新' }));
  await waitFor(() => expect(getMyInvoices).toHaveBeenCalledTimes(2));
});

test('送金ボタンからAPIを呼び出して送金完了まで遷移する', async () => {
  renderNavigator();

  const transferButton = await screen.findByRole('button', { name: '送金する' });
  await waitFor(() => expect(transferButton).toBeEnabled());
  fireEvent.click(transferButton);
  fireEvent.click(await screen.findByRole('button', { name: /佐藤花子/ }));

  fireEvent.change(await screen.findByLabelText('送金金額'), {
    target: { value: '3000' },
  });
  fireEvent.change(screen.getByLabelText('メッセージ（任意）'), {
    target: { value: '昼食代' },
  });
  fireEvent.click(screen.getByRole('button', { name: '送金' }));

  await waitFor(() => {
    expect(createTransfer).toHaveBeenCalledWith(
      '1000002',
      3000,
      '昼食代'
    );
  });
  expect(await screen.findByText('送金が完了しました')).toBeInTheDocument();
  expect(screen.getByText(/33333333-3333-4333-8333-333333333333/)).toBeInTheDocument();
});

test('未ログイン時はログイン画面を表示する', () => {
  useAuth.mockReturnValue({
    session: null,
    initializing: false,
    login: jest.fn(),
    signup: jest.fn(),
    signOut: jest.fn(),
  });

  renderNavigator();

  expect(screen.getByRole('heading', { name: 'ログイン' })).toBeInTheDocument();
  expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
  expect(screen.getByLabelText('パスワード')).toBeInTheDocument();
});
