import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import DashboardPlots from './DashboardPlots';
import FileViewer from './FileViewer';
import ChatInterface from './ChatInterface';
import '../App.css';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { user, logout } = useAuth();

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPlots />;
      case 'files':
        return <FileViewer />;
      case 'chat':
        return <ChatInterface />;
      default:
        return <DashboardPlots />;
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Company Dashboard - {user.company_id}</h1>
        <div>
          <span>Welcome, {user.username}</span>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      <nav className="dashboard-nav">
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button 
          className={activeTab === 'files' ? 'active' : ''}
          onClick={() => setActiveTab('files')}
        >
          Data Files
        </button>
        <button 
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          AI Assistant
        </button>
      </nav>

      <main className="dashboard-content">
        {renderContent()}
      </main>
    </div>
  );
};

export default Dashboard;