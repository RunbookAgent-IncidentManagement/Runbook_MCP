import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, ShieldCheck, UserPlus } from 'lucide-react';
import { useAuth } from './AuthContext';

export default function RegisterPage() {
  const [userId, setUserId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!userId || !email || !password) {
      setError('All fields are required');
      return;
    }
    const result = await register(userId, email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-ink via-[#0b1220] to-[#0a0f1a] px-6">
      <div className="w-full max-w-md bg-white/[0.03] border border-white/[0.08] rounded-3xl p-8 backdrop-blur-xl shadow-2xl shadow-black/30">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal to-coral flex items-center justify-center shadow-lg shadow-teal/20">
            <UserPlus size={20} strokeWidth={2.5} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-serif font-bold text-white">Create Account</h2>
            <p className="text-xs text-mist">Register to manage orders</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="uid" className="block text-xs font-medium text-mist mb-1.5">User ID</label>
            <input
              id="uid" type="text" value={userId} onChange={e => setUserId(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-teal/40 transition"
              placeholder="your-username"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-xs font-medium text-mist mb-1.5">Email</label>
            <input
              id="email" type="email" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-teal/40 transition"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label htmlFor="pwd" className="block text-xs font-medium text-mist mb-1.5">Password</label>
            <input
              id="pwd" type="password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-teal/40 transition"
              placeholder="min 4 chars"
            />
          </div>
          {error && <div className="text-sm text-coral bg-coral/10 border border-coral/20 rounded-lg px-3 py-2">{error}</div>}
          <button type="submit" className="w-full py-3 rounded-full bg-teal text-ink font-bold hover:bg-teal/90 transition shadow-lg shadow-teal/20 flex items-center justify-center gap-2">
            <ShieldCheck size={18} /> Register <ArrowRight size={16} />
          </button>
        </form>
        <div className="mt-6 pt-6 border-t border-white/5 text-center">
          <Link to="/login" className="text-sm text-teal hover:text-white transition font-medium">Already have an account? Sign In</Link>
        </div>
      </div>
    </div>
  );
}
