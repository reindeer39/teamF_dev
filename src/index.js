import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import AppNavigator from './navigation/AppNavigator';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AppNavigator />
  </React.StrictMode>
);
