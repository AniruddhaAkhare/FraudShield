import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import ToastContainer from './components/ToastContainer.jsx'
import { ToastProvider } from './context/ToastContext.jsx'
import LandingPage from './pages/LandingPage.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'

export default function App() {
  return (
    <ToastProvider>
      <Navbar />
      <div className="page-wrapper">
        <Routes>
          <Route path="/"           element={<LandingPage />} />
          <Route path="/analyze"    element={<AnalyzePage />} />
          <Route path="/result/:id" element={<ResultsPage />} />
          <Route path="/history"    element={<HistoryPage />} />
        </Routes>
      </div>
      <ToastContainer />
    </ToastProvider>
  )
}
