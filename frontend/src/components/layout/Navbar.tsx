import { auth } from '../../services/api';
import { useRouter } from 'next/router';

export const Navbar = () => {
  const router = useRouter();

  const handleLogout = () => {
    auth.logout();
    router.push('/login');
  };

  return (
    <nav className="bg-white/70 backdrop-blur-md border-b border-surface-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <span className="font-bold text-2xl bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent">
              WhatsGood
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium text-surface-800 hover:bg-surface-100 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};