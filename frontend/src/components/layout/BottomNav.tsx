import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, FileText, Upload, History, Bell } from 'lucide-react';

const navItems = [
  { name: 'Search', href: '/search', icon: Search },
  { name: 'AI Chat', href: '/ai-chat', icon: FileText },
  { name: 'Documents', href: '/documents', icon: Upload },
  { name: 'History', href: '/history', icon: History },
  { name: 'Alerts', href: '/notifications', icon: Bell },
];

export const BottomNav: React.FC = () => {
  const location = useLocation();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 lg:hidden safe-area-bottom"
      role="navigation"
      aria-label="Mobile navigation"
    >
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;

          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-colors min-w-[64px] ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              aria-label={item.name}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={22} />
              <span className="text-[10px] font-medium">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};