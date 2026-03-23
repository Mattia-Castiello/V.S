/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Watchlist from './components/Watchlist';
import Purchases from './components/Purchases';

export default function App() {
  const [activeTab, setActiveTab] = React.useState('Dashboard');

  const renderView = () => {
    switch (activeTab) {
      case 'Dashboard':
        return <Dashboard />;
      case 'Watchlist':
        return <Watchlist />;
      case 'Purchases':
        return <Purchases />;
      case 'Opportunities':
        return <Dashboard />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderView()}
    </Layout>
  );
}
