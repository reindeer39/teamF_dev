import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import AppNavigator from './navigation/AppNavigator';
import { AuthProvider } from './auth/AuthContext';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AuthProvider>
      <AppNavigator />
    </AuthProvider>
  </React.StrictMode>
);
