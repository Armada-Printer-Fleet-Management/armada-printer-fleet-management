import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { DesktopRouter } from './DesktopRouter';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('#root element is missing from index.html');

createRoot(root).render(
  <StrictMode>
    <DesktopRouter />
  </StrictMode>,
);
