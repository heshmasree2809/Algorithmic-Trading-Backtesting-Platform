import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import MarketExplorerPage from './pages/MarketExplorerPage';
import StrategyLabPage from './pages/StrategyLabPage';
import BacktestResultsPage from './pages/BacktestResultsPage';
import BacktestHistoryPage from './pages/BacktestHistoryPage';
import StrategyComparisonPage from './pages/StrategyComparisonPage';
import RiskAnalysisPage from './pages/RiskAnalysisPage';

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div className="flex min-h-screen bg-terminal-bg">
      <Sidebar />
      <main className="flex-1 p-6 overflow-y-auto">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
        <Route path="/market" element={<ProtectedLayout><MarketExplorerPage /></ProtectedLayout>} />
        <Route path="/strategy-lab" element={<ProtectedLayout><StrategyLabPage /></ProtectedLayout>} />
        <Route path="/backtests/:id" element={<ProtectedLayout><BacktestResultsPage /></ProtectedLayout>} />
        <Route path="/history" element={<ProtectedLayout><BacktestHistoryPage /></ProtectedLayout>} />
        <Route path="/compare" element={<ProtectedLayout><StrategyComparisonPage /></ProtectedLayout>} />
        <Route path="/risk" element={<ProtectedLayout><RiskAnalysisPage /></ProtectedLayout>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
