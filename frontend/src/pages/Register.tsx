import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';
import { Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false
  });

  const [passwordChecks, setPasswordChecks] = useState({
    length: false,
    uppercase: false,
    number: false,
    special: false
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));

    // Update password checks
    if (name === 'password') {
      setPasswordChecks({
        length: value.length >= 8,
        uppercase: /[A-Z]/.test(value),
        number: /[0-9]/.test(value),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(value)
      });
    }
  };

  const validateForm = () => {
    if (!formData.fullName.trim()) {
      toast.error('Full name is required');
      return false;
    }
    if (!formData.email.trim()) {
      toast.error('Email is required');
      return false;
    }
    if (!formData.password) {
      toast.error('Password is required');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return false;
    }
    if (!Object.values(passwordChecks).every(Boolean)) {
      toast.error('Please meet all password requirements');
      return false;
    }
    if (!formData.acceptTerms) {
      toast.error('Please accept the Terms of Service');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    try {
      await register({
        fullName: formData.fullName,
        email: formData.email,
        password: formData.password
      });
      toast.success('Account created successfully! 🎉');
      navigate('/dashboard');
    } catch (error: any) {
      toast.error(error.message || 'Registration failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a1a] flex items-center justify-center p-4">
      <div className="bg-[#1a1a2e] p-8 rounded-xl border border-[#2a2a4a] max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="mb-6 text-center">
          <img src="/jadota-icon.png" alt="JADOTA AI" className="w-16 h-16 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white">Create Account</h2>
          <p className="text-sm text-gray-400">Start trading with JADOTA AI</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Full Name
            </label>
            <input
              type="text"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
              placeholder="John Doe"
              required
            />
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500 pr-10"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute text-gray-400 -translate-y-1/2 right-3 top-1/2 hover:text-white"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            
            {/* Password Requirements */}
            <div className="mt-2 space-y-1 text-xs">
              <PasswordCheck met={passwordChecks.length} text="At least 8 characters" />
              <PasswordCheck met={passwordChecks.uppercase} text="At least one uppercase letter" />
              <PasswordCheck met={passwordChecks.number} text="At least one number" />
              <PasswordCheck met={passwordChecks.special} text="At least one special character" />
            </div>
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500 pr-10"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute text-gray-400 -translate-y-1/2 right-3 top-1/2 hover:text-white"
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              name="acceptTerms"
              checked={formData.acceptTerms}
              onChange={handleChange}
              className="w-4 h-4 accent-[#6366f1]"
              required
            />
            <label className="text-sm text-gray-400">
              I agree to the{' '}
              <a href="/terms" className="text-[#6366f1] hover:text-[#4f46e5]">
                Terms of Service
              </a>
              {' '}and{' '}
              <a href="/privacy" className="text-[#6366f1] hover:text-[#4f46e5]">
                Privacy Policy
              </a>
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-[#6366f1] text-white rounded-lg font-semibold hover:bg-[#4f46e5] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-[#6366f1] hover:text-[#4f46e5] font-medium">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

const PasswordCheck: React.FC<{ met: boolean; text: string }> = ({ met, text }) => (
  <div className="flex items-center gap-2">
    {met ? (
      <CheckCircle className="w-3 h-3 text-green-400" />
    ) : (
      <XCircle className="w-3 h-3 text-gray-500" />
    )}
    <span className={met ? 'text-green-400' : 'text-gray-500'}>{text}</span>
  </div>
);

export default Register;