import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router';

import './index.css';
import AppNavigator from './navigation/AppNavigator';

const root = ReactDOM.createRoot(
  document.getElementById('root')
);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <AppNavigator />
    </BrowserRouter>
  </React.StrictMode>
);
