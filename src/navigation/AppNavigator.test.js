import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AppNavigator from './AppNavigator';
import {
  createTransfer,
  getRecipientInfo,
  getRecipientList,
  getUserSummary,
} from '../api/users';

jest.mock('../api/users');

const summary = {
  account_number: '1000001',
  user_icon: '/icons/user1.png',
  user_name: '山田太郎',
  account_balance: 97000,
};

beforeEach(() => {
  jest.clearAllMocks();
  getUserSummary.mockResolvedValue(summary);
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
});

test('DBから取得した口座情報と操作ボタンを表示する', async () => {
  render(<AppNavigator />);

  expect(await screen.findByText('山田太郎')).toBeInTheDocument();
  expect(screen.getByText('97,000円')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '送金する' })).toBeEnabled();
  expect(screen.getByRole('button', { name: '請求する' })).toBeInTheDocument();
  expect(getUserSummary).toHaveBeenCalledWith('1000001');
});

test('送金ボタンからAPIを呼び出して送金完了まで遷移する', async () => {
  render(<AppNavigator />);

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
      '1000001',
      '1000002',
      3000,
      '昼食代'
    );
  });
  expect(await screen.findByText('送金が完了しました')).toBeInTheDocument();
  expect(screen.getByText(/33333333-3333-4333-8333-333333333333/)).toBeInTheDocument();
});
