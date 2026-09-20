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
import GenericPage from './pages/common/GenericPage';
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
            <Route 
              path="/forecast" 
              element={<GenericPage title="Demand Forecast" description="Multi-horizon demand predictions using statistical, ML, and Prophet models." />} 
            />
            <Route 
              path="/inventory" 
              element={<GenericPage title="Inventory Intelligence" description="Safety stock recommendations, reorder point calculations, and stockout risk alerts." />} 
            />
            <Route 
              path="/trends" 
              element={<GenericPage title="Trends & Anomalies" description="Spike and drop detection, seasonal pattern analysis, and sales anomalies." />} 
            />
            <Route 
              path="/price-insights" 
              element={<GenericPage title="Price Insights" description="Price elasticity modeling and optimal discount recommendations." />} 
            />
            <Route 
              path="/evaluation" 
              element={<GenericPage title="Forecast Evaluation" description="Backtesting reports, WMAPE/RMSE metrics, and drift monitoring." />} 
            />
            <Route 
              path="/assistant" 
              element={<AssistantPage />} 
            />
            <Route path="/auth-test" element={<AuthTestPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
