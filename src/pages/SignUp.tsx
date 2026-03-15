import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'motion/react';
import { signUp, confirmSignUp, resendSignUpCode } from 'aws-amplify/auth';

export default function SignUp() {
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<'SIGN_UP' | 'CONFIRM'>('SIGN_UP');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    // Check if we were redirected here from sign in to confirm
    if (location.state?.step === 'CONFIRM' && location.state?.email) {
      setEmail(location.state.email);
      setStep('CONFIRM');
    }
  }, [location]);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const { isSignUpComplete, nextStep } = await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
            name,
          },
        }
      });

      if (nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        setStep('CONFIRM');
      } else if (isSignUpComplete) {
        navigate('/login');
      }
    } catch (err: any) {
      console.error('Error signing up', err);
      setError(err.message || 'Failed to create account.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const { isSignUpComplete } = await confirmSignUp({
        username: email,
        confirmationCode: code
      });

      if (isSignUpComplete) {
        navigate('/login');
      }
    } catch (err: any) {
      console.error('Error confirming sign up', err);
      setError(err.message || 'Failed to verify code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError('');
    setResendMessage('');
    try {
      await resendSignUpCode({ username: email });
      setResendMessage('Verification code resent successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to resend code.');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center">
            <LayoutDashboard className="w-6 h-6 text-zinc-950" />
          </div>
          <span className="font-bold text-2xl tracking-tight">LimeLight</span>
        </Link>
        <h2 className="text-center text-3xl font-bold tracking-tight text-white">
          {step === 'SIGN_UP' ? 'Create an account' : 'Verify your email'}
        </h2>
        <p className="mt-2 text-center text-sm text-zinc-400">
          {step === 'SIGN_UP' ? (
            <>
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-emerald-500 hover:text-emerald-400 transition-colors">
                Sign in
              </Link>
            </>
          ) : (
            <>
              We sent a verification code to <span className="text-white font-medium">{email}</span>
            </>
          )}
        </p>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md"
      >
        <div className="bg-zinc-900 py-8 px-4 shadow sm:rounded-2xl sm:px-10 border border-zinc-800">
          {step === 'SIGN_UP' ? (
            <form className="space-y-6" onSubmit={handleSignUp}>
              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-rose-400">{error}</p>
                </div>
              )}
              
              <div>
              <label htmlFor="name" className="block text-sm font-medium text-zinc-300">
                Full Name
              </label>
              <div className="mt-2">
                <input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="block w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 sm:text-sm transition-colors"
                  placeholder="Jane Doe"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-zinc-300">
                Email address
              </label>
              <div className="mt-2">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 sm:text-sm transition-colors"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-300">
                Password
              </label>
              <div className="mt-2">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 sm:text-sm transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="flex w-full justify-center items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Creating account...' : (
                  <>Create account <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            </div>
          </form>
          ) : (
            <form className="space-y-6" onSubmit={handleConfirm}>
              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-rose-400">{error}</p>
                </div>
              )}
              {resendMessage && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-emerald-400">{resendMessage}</p>
                </div>
              )}
              
              <div>
                <label htmlFor="code" className="block text-sm font-medium text-zinc-300">
                  Verification Code
                </label>
                <div className="mt-2">
                  <input
                    id="code"
                    name="code"
                    type="text"
                    required
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="block w-full rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 sm:text-sm transition-colors text-center tracking-widest font-mono text-lg"
                    placeholder="000000"
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex w-full justify-center items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Verifying...' : (
                    <>Verify Email <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>
              </div>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={handleResendCode}
                  className="text-sm font-medium text-emerald-500 hover:text-emerald-400 transition-colors"
                >
                  Resend code
                </button>
              </div>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  );
}
