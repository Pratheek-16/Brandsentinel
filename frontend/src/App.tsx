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

  useEffect(() => {
    // Check saved session
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
      } catch {
        localStorage.clear();
      }
    }
  }, []);

  const handleLogin = async (email: string, role: string) => {
    try {
      const res = await api.login(email, 'Demo@12345');
      const token = res.access_token;
      localStorage.setItem('token', token);

      const userObj: User = {
        id: 1, // Demo user mapping
        email,
        name: email.split('@')[0],
        role: role as any,
        workspace_id: 1,
      };
      localStorage.setItem('user', JSON.stringify(userObj));
      setCurrentUser(userObj);
    } catch (err: any) {
      // Offline fallback: if login fails because DB not yet seeded, create local demo session
      const userObj: User = {
        id: 1,
        email,
        name: email.split('@')[0],
        role: role as any,
        workspace_id: 1,
      };
      localStorage.setItem('token', 'mock_jwt_token_demo');
      localStorage.setItem('user', JSON.stringify(userObj));
      setCurrentUser(userObj);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setCurrentUser(null);
  };

  const handleReviewCreated = (contentId: number) => {
    setSelectedContentId(contentId);
    setActiveTab('review');
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Header
        user={currentUser}
        onLogout={handleLogout}
        brand={brand}
        onSelectBrand={setBrand}
        currentTab={activeTab}
        onSelectTab={setActiveTab}
      />

      <main className="flex-1 pb-16" id="main-content">
        {!currentUser ? (
          <LoginScreen onLogin={handleLogin} brand={brand} />
        ) : (
          <div>
            {activeTab === 'submissions' && (
              <ContentEditor onReviewCreated={handleReviewCreated} />
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
