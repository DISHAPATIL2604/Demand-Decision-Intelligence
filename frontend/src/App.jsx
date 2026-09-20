import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/layout/Layout';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import AuthTestPage from './pages/auth/AuthTestPage';
import OverviewPage from './pages/dashboard/OverviewPage';
import UploadPage from './pages/upload/UploadPage';
import ForecastPage from './pages/forecast/ForecastPage';
import InventoryPage from './pages/inventory/InventoryPage';
import AnomalyPage from './pages/anomaly/AnomalyPage';
import PricePage from './pages/price/PricePage';
import EvaluationPage from './pages/evaluation/EvaluationPage';
import AssistantPage from './pages/assistant/AssistantPage';
import './styles/main.css';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected App Routes */}
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<OverviewPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/forecast" element={<ForecastPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/trends" element={<AnomalyPage />} />
            <Route path="/price-insights" element={<PricePage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/auth-test" element={<AuthTestPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
