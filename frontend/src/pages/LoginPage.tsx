import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, Eye, EyeOff, AlertCircle, Fingerprint, Shield, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/state';
import { toast } from 'react-hot-toast';
import { NebulaLogo } from '@/components/NebulaLogo';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore();
  const [isSSOLoading, setIsSSOLoading] = useState(false);
  const [isBiometricLoading, setIsBiometricLoading] = useState(false);
  const [webAuthnEnabled, setWebAuthnEnabled] = useState(false);

  useEffect(() => {
    // Check if WebAuthn is enabled on the backend
    fetch('/api/v1/auth/webauthn/verify/status')
      .then((r) => r.ok ? r.json() : null)
      .then((data) => setWebAuthnEnabled(data?.enabled ?? false))
      .catch(() => {});
  }, []);

  const handleSSOLogin = async () => {
    setIsSSOLoading(true);
    try {
      const resp = await fetch('/api/v1/auth/saml/login');
      const data = await resp.json();
      if (data?.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        toast.error('SAML SSO is not configured');
      }
    } catch {
      toast.error('SAML SSO is not available');
    } finally {
      setIsSSOLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    setIsBiometricLoading(true);
    try {
      // Check if WebAuthn is available in this browser
      if (!window.PublicKeyCredential) {
        toast.error('Biometric authentication is not supported in this browser');
        return;
      }

      // Ask user for email (needed to start WebAuthn login)
      const email = prompt('Enter your email to use biometric login:');
      if (!email) return;

      const startResp = await fetch('/api/v1/auth/webauthn/login/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email }),
      });
      const startData = await startResp.json();
      if (!startResp.ok) {
        toast.error(startData?.detail || 'No biometric credential found');
        return;
      }

      // Convert challenge to ArrayBuffer
      const challenge = Uint8Array.from(atob(startData.challenge), (c) => c.charCodeAt(0));

      // Request biometric assertion
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge,
          rpId: startData.rp_id,
          allowCredentials: [{
            id: Uint8Array.from(atob(startData.credential_id), (c) => c.charCodeAt(0)),
            type: 'public-key',
          }],
        },
      }) as PublicKeyCredential | null;

      if (!assertion) {
        toast.error('Biometric authentication cancelled');
        return;
      }

      // Send assertion to backend
      const authResponse = assertion.response as AuthenticatorAssertionResponse;
      const completeResp = await fetch('/api/v1/auth/webauthn/login/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential_id: startData.credential_id,
          authenticator_data: btoa(String.fromCharCode(...new Uint8Array(authResponse.authenticatorData))),
          client_data_json: btoa(String.fromCharCode(...new Uint8Array(authResponse.clientDataJSON))),
          signature: btoa(String.fromCharCode(...new Uint8Array(authResponse.signature))),
        }),
      });
      const completeData = await completeResp.json();
      if (!completeResp.ok) {
        toast.error(completeData?.detail || 'Biometric login failed');
        return;
      }

      // Store tokens and navigate
      localStorage.setItem('access_token', completeData.access_token);
      localStorage.setItem('refresh_token', completeData.refresh_token);
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Biometric login error:', error);
      toast.error('Biometric login failed');
    } finally {
      setIsBiometricLoading(false);
    }
  };
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (error) {
      toast.error(error);
      clearError();
    }
  }, [error, clearError]);

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    try {
      await login(formData.email, formData.password);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      // Error is handled by the store
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-700 py-12 px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8"
      >
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Link to="/" className="flex items-center gap-3">
            <NebulaLogo size={48} withText={true} textColor="text-gray-900 dark:text-white" />
          </Link>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            Sign in to your Nebula account
          </p>
        </div>

         <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white ${
                  validationErrors.email ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="you@example.com"
              />
            </div>
            {validationErrors.email && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle size={14} />
                {validationErrors.email}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white ${
                  validationErrors.password ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            {validationErrors.password && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle size={14} />
                {validationErrors.password}
              </p>
            )}
          </div>

          {/* Remember me & Forgot password */}
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="rememberMe"
                type="checkbox"
                checked={formData.rememberMe}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Remember me
              </label>
            </div>
            <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700">
              Forgot password?
            </Link>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        {/* Enterprise login options */}
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                or continue with
              </span>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {/* SAML SSO */}
            <button
              onClick={handleSSOLogin}
              disabled={isSSOLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              {isSSOLoading ? <Loader2 className="animate-spin" size={18} /> : <Shield size={18} />}
              Sign in with Enterprise SSO
            </button>

            {/* WebAuthn biometric */}
            {webAuthnEnabled && (
              <button
                onClick={handleBiometricLogin}
                disabled={isBiometricLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                {isBiometricLoading ? <Loader2 className="animate-spin" size={18} /> : <Fingerprint size={18} />}
                Sign in with Biometrics
              </button>
            )}
          </div>
        </div>

        {/* Register link */}
        <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-300">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign up for free
          </Link>
        </p>
      </motion.div>
    </div>
  );
};