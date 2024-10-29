import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { auth } from '../services/api';

const passwordRequirements = {
  minLength: 8,
  hasUpperCase: /[A-Z]/,
  hasNumber: /\d/,
};

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false); // Define loading state
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);

  const validatePassword = (password: string) => {
    const errors = [];
    if (password.length < passwordRequirements.minLength) {
      errors.push('Password must be at least 8 characters long');
    }
    if (!passwordRequirements.hasUpperCase.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    if (!passwordRequirements.hasNumber.test(password)) {
      errors.push('Password must contain at least one number');
    }
    return errors;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'password') {
      setPasswordErrors(validatePassword(value));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true); // Set loading state to true

    // Validate password requirements first
    if (passwordErrors.length > 0) {
      setError('Please fix password requirements');
      setLoading(false);
      return;
    }

    // Check if passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      // Use the auth service instead of direct fetch
      await auth.signup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });

      // Redirect to questionnaire after successful signup
      router.push('/onboarding/questions');
    } catch (err) {
      let errorMessage = 'Signup failed'; // Default error message

      if (isApiError(err)) {
        // Check if the error matches the ApiError structure
        errorMessage = err.response?.data?.detail || errorMessage;
      } else if (err instanceof Error) {
        // If it's a standard error
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false); // Reset loading state
    }
  };

  interface ApiErrorResponse {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

// Type guard to check if the error is of type ApiError
function isApiError(error: unknown): error is ApiErrorResponse {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof (error as { response?: unknown }).response === 'object'
  );
}

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-8">Create Account</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleChange}
              maxLength={50}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your name"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              maxLength={100}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Create a password"
            />
            {passwordErrors.length > 0 && (
              <ul className="mt-2 text-sm text-red-500 space-y-1">
                {passwordErrors.map((error, index) => (
                  <li key={index} className="flex items-center">
                    <span className="mr-2">•</span>
                    {error}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Confirm your password"
            />
          </div>

          {error && (
            <div className="text-red-500 text-sm text-center">{error}</div>
          )}

          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            disabled={loading} // Disable button when loading
          >
            {loading ? 'Signing Up...' : 'Sign Up'} {/* Update button text */}
          </button>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/login" className="text-blue-500 hover:text-blue-600 font-medium">
              Login
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
