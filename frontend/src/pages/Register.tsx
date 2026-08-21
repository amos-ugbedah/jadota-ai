import React from 'react';

const Register: React.FC = () => {
  return (
    <div className="min-h-screen bg-jadota-dark flex items-center justify-center">
      <div className="bg-jadota-card p-8 rounded-xl border border-jadota-border max-w-md w-full">
        <div className="text-center mb-8">
          <img src="/jadota-icon.png" alt="JADOTA AI" className="w-16 h-16 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white">Create Account</h2>
          <p className="text-gray-400 text-sm">Start trading with JADOTA AI</p>
        </div>
        <form className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Full Name</label>
            <input
              type="text"
              className="w-full px-4 py-2 bg-jadota-dark border border-jadota-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input
              type="email"
              className="w-full px-4 py-2 bg-jadota-dark border border-jadota-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input
              type="password"
              className="w-full px-4 py-2 bg-jadota-dark border border-jadota-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-primary-500 text-white rounded-lg font-semibold hover:bg-primary-600 transition"
          >
            Create Account
          </button>
        </form>
        <p className="text-center text-gray-400 text-sm mt-6">
          Already have an account?{' '}
          <a href="/login" className="text-primary-400 hover:text-primary-300">
            Sign In
          </a>
        </p>
      </div>
    </div>
  );
};

export default Register;