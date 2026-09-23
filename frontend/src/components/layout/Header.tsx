import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu,
  X,
  User,
  LogOut,
  Settings,
  Bell,
  Upload,
  FileText,
  BarChart3,
  Moon,
  Sun,
  Search,
} from 'lucide-react';
import { useAuthStore } from '@/state';
import { useNotificationStore } from '@/state';
import { useSettingsStore } from '@/state';
import { useAuth } from '@/context/AuthContext';
import { NebulaLogo } from '@/components/NebulaLogo';

interface HeaderProps {
  onMenuToggle: () => void;
  isMobileMenuOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle, isMobileMenuOpen }) => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { unreadCount } = useNotificationStore();
  const { theme, setTheme } = useSettingsStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { isGuest } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and mobile menu button */}
          <div className="flex items-center gap-4">
            <button
              onClick={onMenuToggle}
              className="lg:hidden p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            
            <Link to="/" className="flex items-center gap-2">
              <NebulaLogo size={32} withText={false} />
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                Nebula
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          {isAuthenticated && (
            <nav className="hidden lg:flex items-center gap-6">
              <Link
                to="/search"
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white flex items-center gap-2"
              >
                <Search size={18} />
                Search
              </Link>
              <Link
                to="/ai-chat"
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white flex items-center gap-2"
              >
                <FileText size={18} />
                AI Chat
              </Link>
              <Link
                to="/documents"
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white flex items-center gap-2"
              >
                <Upload size={18} />
                Documents
              </Link>
              <Link
                to="/analytics"
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white flex items-center gap-2"
              >
                <BarChart3 size={18} />
                Analytics
              </Link>
            </nav>
          )}

          {/* Right side actions */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                {/* Guest badge */}
                {isGuest && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-xs font-medium rounded-full">
                    Guest
                  </span>
                )}

                {/* Theme toggle */}
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>

                {/* Notifications */}
                <Link
                  to="/notifications"
                  className="relative p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Bell size={20} />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {unreadCount}
                    </span>
                  )}
                </Link>

                {/* User menu */}
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <User size={20} className="text-gray-600 dark:text-gray-300" />
                    <span className="hidden sm:block text-sm text-gray-700 dark:text-gray-300">
                      {user?.email}
                    </span>
                  </button>

                  <AnimatePresence>
                    {showUserMenu && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50"
                      >
                        <Link
                          to="/settings"
                          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                          onClick={() => setShowUserMenu(false)}
                        >
                          <Settings size={16} />
                          Settings
                        </Link>
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <LogOut size={16} />
                          Logout
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};