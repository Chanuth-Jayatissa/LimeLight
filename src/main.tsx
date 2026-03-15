import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import App from './App.tsx';
import './index.css';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_USER_POOL_ID || 'us-east-2_sVYudZu6m',
      userPoolClientId: import.meta.env.VITE_APP_CLIENT_ID || '4675h0fa8h36amb12biu5hitej',
    }
  }
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
