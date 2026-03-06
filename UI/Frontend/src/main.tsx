import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { PaperQuantProvider } from './context/PaperQuantContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PaperQuantProvider>
      <App />
    </PaperQuantProvider>
  </StrictMode>,
)
