import { createContext, useContext, useEffect, useState } from 'react';
import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  signup as signupRequest,
} from '../api/auth';
import {
  clearStoredToken,
  getStoredToken,
  storeToken,
} from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    let active = true;
    if (!getStoredToken()) {
      setInitializing(false);
      return undefined;
    }

    getCurrentUser()
      .then((data) => {
        if (active) setSession(data);
      })
      .catch(() => {
        clearStoredToken();
      })
      .finally(() => {
        if (active) setInitializing(false);
      });

    return () => {
      active = false;
    };
  }, []);

  async function authenticate(requestFunction, values) {
    const data = await requestFunction(values);
    storeToken(data.token);
    const nextSession = { email: data.email, account: data.account };
    setSession(nextSession);
    return nextSession;
  }

  async function signOut() {
    try {
      await logoutRequest();
    } catch {
      // APIへ接続できない場合も、端末上のログイン状態は確実に破棄する。
    } finally {
      clearStoredToken();
      setSession(null);
    }
  }

  const value = {
    session,
    initializing,
    login: (values) => authenticate(loginRequest, values),
    signup: (values) => authenticate(signupRequest, values),
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
