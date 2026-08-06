import { useState } from 'react';
import './AuthScreen.css';

function AuthScreen({ onLogin, onSignup }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userName, setUserName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      if (mode === 'login') {
        await onLogin({ email, password });
      } else {
        await onSignup({ email, password, user_name: userName });
      }
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError('');
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
              <label htmlFor="auth-user-name">表示名</label>
              <input
                id="auth-user-name"
                value={userName}
                onChange={(event) => setUserName(event.target.value)}
                autoComplete="name"
                maxLength="100"
                required
              />
            </>
          )}

          <label htmlFor="auth-email">メールアドレス</label>
          <input
            id="auth-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="username"
            required
          />

          <label htmlFor="auth-password">パスワード</label>
          <input
            id="auth-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            required
          />

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
