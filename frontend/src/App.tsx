import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { LoginScreen } from './components/LoginScreen';
import { ContentEditor } from './components/ContentEditor';
import { ReviewScreen } from './components/ReviewScreen';
import { KnowledgeBaseScreen } from './components/KnowledgeBaseScreen';
import { VisionInspectorScreen } from './components/VisionInspectorScreen';
import { AuditTrailScreen } from './components/AuditTrailScreen';
import { InsightsScreen } from './components/InsightsScreen';
import { User } from './types';
import { api } from './api';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [brand, setBrand] = useState('NovaFit');
  const [activeTab, setActiveTab] = useState('submissions');
  const [selectedContentId, setSelectedContentId] = useState<number | null>(null);
  const [loadingSession, setLoadingSession] = useState(true);

  useEffect(() => {
    // Validate existing session against /auth/me
    const token = localStorage.getItem('token');
    if (token) {
      api
        .getMe()
        .then((user) => {
          setCurrentUser(user);
          if (user.workspace_name) {
            setBrand(user.workspace_name);
          }
        })
        .catch(() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setCurrentUser(null);
        })
        .finally(() => {
          setLoadingSession(false);
        });
    } else {
      setLoadingSession(false);
    }
  }, []);

  const handleLoginSuccess = (token: string, user: User) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    setCurrentUser(user);
    if (user.workspace_name) {
      setBrand(user.workspace_name);
    }
    setActiveTab('submissions');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setCurrentUser(null);
  };

  const handleReviewCreated = (contentId: number) => {
    setSelectedContentId(contentId);
    setActiveTab('review');
  };

  const handleBrandChange = (newBrand: string) => {
    setBrand(newBrand);
  };

  if (loadingSession) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-slate-400 text-sm font-mono">
        Authenticating BrandSentinel workspace session...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Header
        user={currentUser}
        onLogout={handleLogout}
        brand={brand}
        onSelectBrand={handleBrandChange}
        currentTab={activeTab}
        onSelectTab={setActiveTab}
      />

      <main className="flex-1 pb-16" id="main-content">
        {!currentUser ? (
          <LoginScreen
            onLoginSuccess={handleLoginSuccess}
            brand={brand}
            onSelectBrand={handleBrandChange}
          />
        ) : (
          <div>
            {activeTab === 'submissions' && (
              <ContentEditor
                brand={brand}
                onReviewCreated={handleReviewCreated}
              />
            )}
            {activeTab === 'review' && (
              <ReviewScreen
                contentId={selectedContentId || 1}
                currentUser={currentUser}
                onRefreshContent={() => {}}
              />
            )}
            {activeTab === 'kb' && <KnowledgeBaseScreen />}
            {activeTab === 'vision' && <VisionInspectorScreen />}
            {activeTab === 'audit' && <AuditTrailScreen />}
            {activeTab === 'insights' && <InsightsScreen />}
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
