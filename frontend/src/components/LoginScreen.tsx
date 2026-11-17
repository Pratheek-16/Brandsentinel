import React, { useState } from 'react';
import { Shield, KeyRound, UserCheck, AlertCircle } from 'lucide-react';

interface LoginScreenProps {
  onLogin: (email: string, role: string) => void;
  brand: string;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin, brand }) => {
  const brandDomain = brand.toLowerCase().replace(/\s+/g, '');
  const [email, setEmail] = useState(`creator1@${brandDomain}.local`);
  const [password, setPassword] = useState('Demo@12345');
  const [error, setError] = useState<string | null>(null);

  const demoAccounts = [
    { label: 'Creator 1', email: `creator1@${brandDomain}.local`, role: 'creator' },
    { label: 'Creator 2', email: `creator2@${brandDomain}.local`, role: 'creator' },
    { label: 'Manager', email: `manager@${brandDomain}.local`, role: 'manager' },
    { label: 'Reviewer', email: `reviewer@${brandDomain}.local`, role: 'reviewer' },
    { label: 'Admin (Guardian)', email: `admin@${brandDomain}.local`, role: 'admin' },
  ];

  const handleQuickSelect = (acc: typeof demoAccounts[0]) => {
    setEmail(acc.email);
    setPassword('Demo@12345');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please provide an email address.');
      return;
    }
    const matched = demoAccounts.find((a) => a.email.toLowerCase() === email.toLowerCase());
    const role = matched ? matched.role : 'creator';
    onLogin(email, role);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg border border-slate-200">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100 text-blue-600">
            <Shield className="h-6 w-6" aria-hidden="true" />
          </div>
          <h2 className="mt-4 text-2xl font-bold text-slate-900 tracking-tight">Sign in to BrandSentinel</h2>
          <p className="mt-1 text-xs text-slate-500">
            Active Brand Kit: <span className="font-semibold text-blue-600">{brand}</span>
          </p>
        </div>

        {/* Quick Demo Switcher */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Demo Persona Switcher (Password: Demo@12345)
          </label>
          <div className="grid grid-cols-2 gap-2">
            {demoAccounts.map((acc) => (
              <button
                key={acc.email}
                type="button"
                onClick={() => handleQuickSelect(acc)}
                className={`px-2.5 py-1.5 text-xs font-medium rounded-md border text-left transition-colors ${
                  email === acc.email
                    ? 'border-blue-600 bg-blue-50 text-blue-800 ring-1 ring-blue-600'
                    : 'border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700'
                }`}
              >
                <div className="font-semibold">{acc.label}</div>
                <div className="text-[10px] text-slate-500 truncate">{acc.email}</div>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-center space-x-2 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-xs font-medium text-slate-700">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="password-field" className="block text-xs font-medium text-slate-700">
              Password
            </label>
            <input
              id="password-field"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Authenticate Session
          </button>
        </form>
      </div>
    </div>
  );
};
