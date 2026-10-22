import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { BottomNav } from './BottomNav';
import { useOfflineStore } from '@/state';
import { WifiOff } from 'lucide-react';

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { isOnline } = useOfflineStore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-16 lg:pb-0">
      {/* Skip navigation link for accessibility */}
      <a
        href="#main-content"
        className="skip-nav"
      >
        Skip to main content
      </a>

      <Header 
        onMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
        isMobileMenuOpen={isMobileMenuOpen}
      />
      
      <div className="flex">
        <Sidebar 
          isOpen={isMobileMenuOpen} 
          onClose={() => setIsMobileMenuOpen(false)} 
        />
        
        <main id="main-content" className="flex-1 p-6 lg:p-8" role="main" tabIndex={-1}>
          {/* Offline banner */}
          {!isOnline && (
            <div 
              className="mb-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 flex items-center gap-3"
              role="alert"
              aria-live="polite"
            >
              <WifiOff className="text-yellow-600 dark:text-yellow-400 shrink-0" size={20} />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  You're offline
                </p>
                <p className="text-xs text-yellow-600 dark:text-yellow-300">
                  Some features may be limited. Changes will sync when you reconnect.
                </p>
              </div>
            </div>
          )}
          
          {children}
        </main>
      </div>

      {/* Mobile bottom navigation */}
      <BottomNav />
    </div>
  );
};
