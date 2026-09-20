import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const titleMap = {
  '/dashboard': 'Store & Business Overview',
  '/upload': 'Upload Daily Sales Sheet',
  '/forecast': 'Sales Demand Predictions',
  '/inventory': 'Stock & Reorder Decision Planner',
  '/trends': 'Surge Spikes & Stockout Alerts',
  '/price-insights': 'Market Prices & Discount Elasticity',
  '/evaluation': 'Forecast Model Accuracy Check',
  '/assistant': 'AI Business Decision Advisor',
};

export default function Layout() {
  const location = useLocation();
  const pageTitle = titleMap[location.pathname] || 'Demand Decision Intelligence';

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content-area">
        <Header title={pageTitle} />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
