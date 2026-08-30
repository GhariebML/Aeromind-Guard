import React, { useState } from 'react';
import { ShieldAlert, Lock, User as UserIcon, Loader2 } from 'lucide-react';
import { useAuth } from '../services/authContext';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@aeromind.local');
  const [password, setPassword] = useState('admin123');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Invalid credentials. Access denied.');
        } else if (response.status === 502 || response.status === 503) {
          throw new Error('Backend services unavailable. Please check system health.');
        } else {
          throw new Error('Authentication failed.');
        }
      }

      const data = await response.json();
      if (data.access_token) {
        login(data.access_token, data.role);
      } else {
        throw new Error('Invalid authentication response format.');
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>
      
      <div className="relative z-10 w-full max-w-md">
        <div className="glass-premium rounded-2xl p-8 border border-slate-800/60 shadow-2xl shadow-cyan-900/10">
          
          {/* Logo Section */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-[0_0_30px_rgba(34,211,238,0.4)] border border-cyan-400/30 mb-4 animate-float">
              <ShieldAlert className="w-8 h-8 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]" />
            </div>
            <h1 className="text-2xl font-extrabold tracking-widest text-gradient-cyan text-center">
              AEROMIND
            </h1>
            <h2 className="text-sm font-bold text-slate-400 tracking-wider mt-1">
              CLIMATEGUARD
            </h2>
            <div className="mt-2 text-[10px] text-cyan-500 font-mono tracking-widest border border-cyan-900/50 bg-cyan-950/30 px-2 py-0.5 rounded">
              RESTRICTED ACCESS
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-rose-950/50 border border-rose-500/50 flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
              <span className="text-xs text-rose-300 font-medium">{error}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono font-bold text-slate-400 mb-1.5 uppercase tracking-wider">
                Operator Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <UserIcon className="h-4 w-4 text-slate-500" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg text-sm text-slate-200 focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-colors"
                  placeholder="operator@aeromind.local"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold text-slate-400 mb-1.5 uppercase tracking-wider">
                Passcode
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-slate-500" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg text-sm text-slate-200 focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-6 py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-sm font-bold tracking-wide shadow-lg shadow-cyan-900/20 transition-all transform hover:-translate-y-0.5 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  AUTHENTICATING...
                </>
              ) : (
                'SECURE LOGIN'
              )}
            </button>
          </form>

          {/* Footer Info */}
          <div className="mt-8 text-center text-[10px] text-slate-500 font-mono flex flex-col gap-1">
            <p>UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED</p>
            <p className="opacity-60">AeroMind Operations Center v2.4.0</p>
          </div>
        </div>
      </div>
    </div>
  );
};
