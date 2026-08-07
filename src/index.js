import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import './index.css';
import AppNavigator from './navigation/AppNavigator';
import { AuthProvider } from './auth/AuthContext';

const root = ReactDOM.createRoot(
  document.getElementById('root')
);

root.render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <AppNavigator />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
