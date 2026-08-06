import { useState } from 'react';
import './AuthScreen.css';

function AuthScreen({ onLogin, onSignup }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userName, setUserName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    setFieldErrors({});
    try {
      if (mode === 'login') {
        await onLogin({ email, password });
      } else {
        await onSignup({
          account_number: accountNumber,
          user_name: userName,
          email,
          password,
        });
      }
    } catch (apiError) {
      const responseErrors = apiError.data || {};
      const nextFieldErrors = responseErrors.errors || responseErrors;
      const knownFields = ['account_number', 'user_name', 'email', 'password'];
      const hasFieldErrors = knownFields.some((field) => nextFieldErrors[field]);
      if (hasFieldErrors) {
        setFieldErrors(nextFieldErrors);
      } else {
        setError(apiError.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError('');
    setFieldErrors({});
  }

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <p className="auth-card__eyebrow">Team F Wallet</p>
        <h1>{mode === 'login' ? 'ログイン' : '新規登録'}</h1>
        <p className="auth-card__description">
          {mode === 'login'
            ? 'ログインすると口座のトップ画面へ移動します。'
            : 'ログイン情報と送金口座を同時に作成します。'}
        </p>

        <div className="auth-tabs" role="tablist" aria-label="認証方法">
          <button
            type="button"
            className={mode === 'login' ? 'auth-tab auth-tab--active' : 'auth-tab'}
            onClick={() => switchMode('login')}
          >
            ログイン
          </button>
          <button
            type="button"
            className={mode === 'signup' ? 'auth-tab auth-tab--active' : 'auth-tab'}
            onClick={() => switchMode('signup')}
          >
            新規登録
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <>
              <label htmlFor="auth-account-number">口座番号</label>
              <input
                id="auth-account-number"
                value={accountNumber}
                onChange={(event) => setAccountNumber(event.target.value)}
                inputMode="numeric"
                pattern="[0-9]{7}"
                maxLength="7"
                autoComplete="off"
                aria-describedby={fieldErrors.account_number ? 'auth-account-number-error' : undefined}
                aria-invalid={Boolean(fieldErrors.account_number)}
                required
              />
              {fieldErrors.account_number && (
                <p id="auth-account-number-error" className="auth-form__field-error" role="alert">
                  {fieldErrors.account_number.join(' ')}
                </p>
              )}

              <label htmlFor="auth-user-name">表示名</label>
              <input
                id="auth-user-name"
                value={userName}
                onChange={(event) => setUserName(event.target.value)}
                autoComplete="name"
                maxLength="100"
                aria-describedby={fieldErrors.user_name ? 'auth-user-name-error' : undefined}
                aria-invalid={Boolean(fieldErrors.user_name)}
                required
              />
              {fieldErrors.user_name && (
                <p id="auth-user-name-error" className="auth-form__field-error" role="alert">
                  {fieldErrors.user_name.join(' ')}
                </p>
              )}
            </>
          )}

          <label htmlFor="auth-email">メールアドレス</label>
          <input
            id="auth-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="username"
            aria-describedby={fieldErrors.email ? 'auth-email-error' : undefined}
            aria-invalid={Boolean(fieldErrors.email)}
            required
          />
          {fieldErrors.email && (
            <p id="auth-email-error" className="auth-form__field-error" role="alert">
              {fieldErrors.email.join(' ')}
            </p>
          )}

          <label htmlFor="auth-password">パスワード</label>
          <input
            id="auth-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            aria-describedby={fieldErrors.password ? 'auth-password-error' : undefined}
            aria-invalid={Boolean(fieldErrors.password)}
            required
          />
          {fieldErrors.password && (
            <p id="auth-password-error" className="auth-form__field-error" role="alert">
              {fieldErrors.password.join(' ')}
            </p>
          )}

          {error && <p className="auth-form__error" role="alert">{error}</p>}
          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting
              ? '処理中...'
              : mode === 'login' ? 'ログイン' : 'アカウントを作成'}
          </button>
        </form>

      </section>
    </main>
  );
}

export default AuthScreen;
