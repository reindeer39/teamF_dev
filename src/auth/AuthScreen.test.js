import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AuthScreen from './AuthScreen';


test('新規登録で口座番号・表示名・メールアドレス・パスワードを送信する', async () => {
  const onSignup = jest.fn().mockResolvedValue({});

  render(<AuthScreen onLogin={jest.fn()} onSignup={onSignup} />);
  fireEvent.click(screen.getByRole('button', { name: '新規登録' }));
  fireEvent.change(screen.getByLabelText('口座番号'), {
    target: { value: '1234567' },
  });
  fireEvent.change(screen.getByLabelText('表示名'), {
    target: { value: '山田太郎' },
  });
  fireEvent.change(screen.getByLabelText('メールアドレス'), {
    target: { value: 'yamada@example.com' },
  });
  fireEvent.change(screen.getByLabelText('パスワード'), {
    target: { value: 'Correct-Horse-57!' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'アカウントを作成' }));

  await waitFor(() => {
    expect(onSignup).toHaveBeenCalledWith({
      account_number: '1234567',
      user_name: '山田太郎',
      email: 'yamada@example.com',
      password: 'Correct-Horse-57!',
    });
  });
});


test('新規登録APIのフィールド別エラーを各入力欄の近くへ表示する', async () => {
  const apiError = new Error('登録できませんでした。');
  apiError.data = {
    account_number: ['この口座番号は既に使用されています。'],
    email: ['このメールアドレスは既に使用されています。'],
  };
  const onSignup = jest.fn().mockRejectedValue(apiError);

  render(<AuthScreen onLogin={jest.fn()} onSignup={onSignup} />);
  fireEvent.click(screen.getByRole('button', { name: '新規登録' }));
  fireEvent.change(screen.getByLabelText('口座番号'), {
    target: { value: '1234567' },
  });
  fireEvent.change(screen.getByLabelText('表示名'), {
    target: { value: '山田太郎' },
  });
  fireEvent.change(screen.getByLabelText('メールアドレス'), {
    target: { value: 'yamada@example.com' },
  });
  fireEvent.change(screen.getByLabelText('パスワード'), {
    target: { value: 'Correct-Horse-57!' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'アカウントを作成' }));

  expect(
    await screen.findByText('この口座番号は既に使用されています。')
  ).toBeInTheDocument();
  expect(
    screen.getByText('このメールアドレスは既に使用されています。')
  ).toBeInTheDocument();
  expect(screen.getByLabelText('口座番号')).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByLabelText('メールアドレス')).toHaveAttribute('aria-invalid', 'true');
});
