import React, { useState, useEffect } from 'react';
import { NavigationRail } from './components/NavigationRail';
import { PageTopStrip, WorkflowStep } from './components/PageTopStrip';
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
      <div
        className="min-h-screen flex items-center justify-center text-xs font-mono"
        style={{
          backgroundColor: 'var(--paper)',
          color: 'var(--graphite)',
          backgroundImage: 'var(--paper-grain)',
        }}
      >
        <span>Opening BrandSentinel proofing desk session...</span>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <LoginScreen
        onLoginSuccess={handleLoginSuccess}
        brand={brand}
        onSelectBrand={handleBrandChange}
      />
    );
  }

  // Derive page metadata for in-page Top Strip
  const getPageMeta = (): {
    title: string;
    category: string;
    step?: WorkflowStep;
    nextStepText?: string;
  } => {
    switch (activeTab) {
      case 'submissions':
        return {
          title: 'Drafts & proofing desk',
          category: 'Authoring',
          step: 'draft',
          nextStepText:
            'Write or paste copy on the sheet, or upload an asset, then click "Check draft".',
        };
      case 'review':
        return {
          title: 'The proofing desk',
          category: 'Editorial review',
          step: 'checked',
          nextStepText:
            'Review margin annotation cards, accept or edit suggested rewrites, then submit for sign-off.',
        };
      case 'kb':
        return {
          title: 'Brand rules & knowledge base',
          category: 'Governance rules',
          nextStepText:
            'Manage approved brand facts, terminology, and test sentences live against active rules.',
        };
      case 'vision':
        return {
          title: 'Visual & color compliance',
          category: 'Asset audit',
          nextStepText:
            'Upload creative images to verify CIE2000 palette distances and WCAG 2.2 contrast.',
        };
      case 'audit':
        return {
          title: 'Cryptographic audit ledger',
          category: 'Provenance',
          nextStepText:
            'Verify SHA-256 sequential block hashes to guarantee platform tamper resistance.',
        };
      case 'insights':
        return {
          title: 'Governance insights & ambiguity',
          category: 'Intelligence',
          nextStepText:
            'Review pass rates and accept suggested rule clarifications to eliminate ambiguity.',
        };
      default:
        return {
          title: 'BrandSentinel console',
          category: 'Workspace',
        };
    }
  };

  const pageMeta = getPageMeta();

  return (
    <div
      className="h-screen w-screen overflow-hidden flex flex-row"
      style={{
        backgroundColor: 'var(--paper)',
        backgroundImage: 'var(--paper-grain)',
        color: 'var(--ink)',
      }}
    >
      {/* Editorial Left Rail - Permanently fixed and docked to viewport */}
      <NavigationRail
        user={currentUser}
        brand={brand}
        onSelectBrand={handleBrandChange}
        currentTab={activeTab}
        onSelectTab={setActiveTab}
        onLogout={handleLogout}
      />

      {/* Main Editorial Canvas - Scrolls independently on the right */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        <PageTopStrip
          title={pageMeta.title}
          category={pageMeta.category}
          currentStep={pageMeta.step}
          nextStepText={pageMeta.nextStepText}
          onHelpClick={() => {
            alert(
              'BrandSentinel Proofing Desk:\n• J / K: Navigate margin annotations\n• A: Apply verified fix\n• E: Custom edit\n• D: Dismiss with justification\n• PII is always masked prior to LLM evaluation.'
            );
          }}
        />

        <main className="flex-1 pb-16 overflow-y-auto" id="main-content">
          {activeTab === 'submissions' && (
            <ContentEditor brand={brand} onReviewCreated={handleReviewCreated} />
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
        </main>
      </div>
    </div>
  );
};

export default App;
