import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { api } from './api';
import { Layout } from './components/Layout';
import { CascadePage } from './pages/CascadePage';
import { DashboardPage } from './pages/DashboardPage';
import { EvaluatePage } from './pages/EvaluatePage';
import { GeneratePage } from './pages/GeneratePage';
import { MaturityPage } from './pages/MaturityPage';
import type { HealthResponse } from './types';

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <Layout health={health}>
      <Routes>
        <Route path="/" element={<Navigate to="/evaluate" replace />} />
        <Route path="/evaluate" element={<EvaluatePage />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/cascade" element={<CascadePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/maturity" element={<MaturityPage />} />
      </Routes>
    </Layout>
  );
}
