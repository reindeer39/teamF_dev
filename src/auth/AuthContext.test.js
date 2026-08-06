import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { getCurrentUser, login, logout, signup } from '../api/auth';

jest.mock('../api/auth');

const sessionResponse = {
  email: 'yamada@example.com',
  account: {
    account_number: '1000001',
    user_name: '山田太郎',
    account_balance: 97000,
  },
};

function AuthProbe() {
  const auth = useAuth();
  if (auth.initializing) return <p>確認中</p>;
  if (auth.session) return <p>ログイン中: {auth.session.account.user_name}</p>;
  return (
    <button
      type="button"
      onClick={() => auth.login({ email: 'yamada@example.com', password: 'password' })}
    >
      テストログイン
    </button>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  window.localStorage.clear();
  logout.mockResolvedValue(null);
  signup.mockResolvedValue(null);
});

test('ログイン成功後にトークンを保存して認証状態へ遷移する', async () => {
  login.mockResolvedValue({ token: 'saved-token', ...sessionResponse });

  render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>
  );
  fireEvent.click(await screen.findByRole('button', { name: 'テストログイン' }));

  expect(await screen.findByText('ログイン中: 山田太郎')).toBeInTheDocument();
  expect(window.localStorage.getItem('teamf.authToken')).toBe('saved-token');
});

test('保存済みトークンがあれば再読み込み時にログイン状態を復元する', async () => {
  window.localStorage.setItem('teamf.authToken', 'existing-token');
  getCurrentUser.mockResolvedValue(sessionResponse);

  render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>
  );

  expect(await screen.findByText('ログイン中: 山田太郎')).toBeInTheDocument();
  await waitFor(() => expect(getCurrentUser).toHaveBeenCalledTimes(1));
});
