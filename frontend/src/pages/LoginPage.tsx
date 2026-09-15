import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Stethoscope, AlertCircle } from 'lucide-react';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      // Navigate based on role stored
      const user = JSON.parse(localStorage.getItem('careroute_user') || '{}');
      if (user.role === 'doctor') navigate('/doctor');
      else if (user.role === 'admin') navigate('/admin');
      else if (user.role === 'community_authority') navigate('/community');
      else navigate('/patient');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-healthcare-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Stethoscope className="text-primary-600" size={32} />
            <span className="text-2xl font-bold text-gray-900">CareRoute AI</span>
          </div>
          <p className="text-gray-600">Sign in to your account</p>
        </div>
        <div className="card">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm text-red-700">
              <AlertCircle size={16} /> {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" className="input-field" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" className="input-field" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Enter password" />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          <div className="mt-4 text-center text-sm text-gray-600">
            Don't have an account? <Link to="/register" className="text-primary-600 font-medium hover:underline">Register</Link>
          </div>
        </div>
        <div className="mt-6 card bg-gray-50 text-sm">
          <p className="font-medium text-gray-700 mb-2">Demo Accounts:</p>
          <div className="space-y-1 text-gray-600">
            <p>Patient: <code>fowmiya@demo.com</code> / <code>patient123</code></p>
            <p>Doctor: <code>dr.arun@demo.com</code> / <code>doctor123</code></p>
            <p>Admin: <code>admin@careroute.demo</code> / <code>admin123</code></p>
          </div>
        </div>
      </div>
    </div>
  );
}
