import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, User, Bell, Shield, Palette, Globe, Save, BellRing, Smartphone } from 'lucide-react';
import { useSettingsStore } from '@/state';
import { useAuthStore } from '@/state';
import { toast } from 'react-hot-toast';

export const SettingsPage: React.FC = () => {
  const { settings, theme, language, fetchSettings, updateSettings, setTheme, setLanguage, clearError } = useSettingsStore();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [pushRegistered, setPushRegistered] = useState(false);
  const [isRegisteringPush, setIsRegisteringPush] = useState(false);
  const [devices, setDevices] = useState<Array<{session_id: string; device_name: string; is_active: boolean}>>([]);

  useEffect(() => {
    fetchSettings();

    // Check push notification registration status
    fetch('/api/v1/notifications/push/status')
      .then((r) => r.ok ? r.json() : null)
      .then((data) => { if (data) setPushRegistered(data.registered); })
      .catch(() => {});

    // Fetch federated search devices
    fetch('/api/v1/search/federated/devices')
      .then((r) => r.ok ? r.json() : null)
      .then((data) => { if (data?.devices) setDevices(data.devices); })
      .catch(() => {});
  }, [fetchSettings]);

  const handleRegisterPush = async () => {
    setIsRegisteringPush(true);
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        toast.error('Push notifications are not supported in this browser');
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        toast.error('Push notification permission denied');
        return;
      }
      const registration = await navigator.serviceWorker.register('/sw.js');
      const subscription = await registration.pushManager.subscribe({ userVisibleOnly: true });
      const token = btoa(JSON.stringify(subscription)).replace(/=/g, '');

      const resp = await fetch('/api/v1/notifications/push/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, platform: 'web' }),
      });
      if (resp.ok) {
        setPushRegistered(true);
        toast.success('Push notifications enabled');
      } else {
        const data = await resp.json();
        toast.error(data?.detail || 'Failed to register for push');
      }
    } catch (error) {
      toast.error('Failed to enable push notifications');
    } finally {
      setIsRegisteringPush(false);
    }
  };

  const handleRemoveDevice = async (sessionId: string) => {
    try {
      const resp = await fetch(`/api/v1/search/federated/devices/${sessionId}`, { method: 'DELETE' });
      if (resp.ok) {
        setDevices((prev) => prev.filter((d) => d.session_id !== sessionId));
        toast.success('Device removed');
      }
    } catch {
      toast.error('Failed to remove device');
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateSettings({
        profile: {
          email: user?.email,
          display_name: user?.email?.split('@')[0],
        },
      });
      toast.success('Profile updated successfully');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    toast.success('Theme updated');
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'appearance', name: 'Appearance', icon: Palette },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'privacy', name: 'Privacy', icon: Shield },
    { id: 'language', name: 'Language', icon: Globe },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4 sm:space-y-6 px-2 sm:px-0">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
        {/* Tabs — horizontal scroll on mobile */}
        <div className="lg:w-64 flex lg:flex-col gap-1 overflow-x-auto pb-2 lg:pb-0 lg:overflow-x-visible">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-shrink-0 flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-3 rounded-lg transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <Icon size={18} />
                <span className="font-medium text-sm sm:text-base">{tab.name}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          {activeTab === 'profile' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Profile Information
              </h2>
              <form onSubmit={handleSaveProfile} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    defaultValue={user?.email?.split('@')[0]}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  <Save size={18} />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </form>
            </motion.div>
          )}

          {activeTab === 'appearance' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Appearance
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Theme
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { value: 'light', label: 'Light', icon: '☀️' },
                      { value: 'dark', label: 'Dark', icon: '🌙' },
                      { value: 'system', label: 'System', icon: '💻' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => handleThemeChange(option.value as 'light' | 'dark' | 'system')}
                        className={`p-4 rounded-lg border-2 transition-colors ${
                          theme === option.value
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <div className="text-2xl mb-2">{option.icon}</div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {option.label}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'notifications' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Notification Settings
              </h2>
              <div className="space-y-4">
                {[
                  { id: 'email_notifications', label: 'Email Notifications', description: 'Receive email updates' },
                  { id: 'search_alerts', label: 'Search Alerts', description: 'Get notified about search results' },
                ].map((setting) => (
                  <div
                    key={setting.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{setting.label}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{setting.description}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                ))}

                {/* Push Notification Registration */}
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-3">
                    <BellRing className="text-blue-600 dark:text-blue-400" size={20} />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">Push Notifications</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {pushRegistered ? 'Push notifications are enabled' : 'Receive instant push notifications'}
                      </p>
                    </div>
                    {!pushRegistered && (
                      <button
                        onClick={handleRegisterPush}
                        disabled={isRegisteringPush}
                        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                      >
                        {isRegisteringPush ? 'Enabling...' : 'Enable'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'privacy' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Privacy & Security
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Search History</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Save your search history</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Analytics</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Help improve Nebula with usage analytics</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {/* Federated Search Devices */}
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-3 mb-4">
                    <Smartphone className="text-blue-600 dark:text-blue-400" size={20} />
                    <h3 className="font-medium text-gray-900 dark:text-white">Connected Devices</h3>
                  </div>
                  {devices.length === 0 ? (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      No devices connected for federated search
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {devices.map((device) => (
                        <div
                          key={device.session_id}
                          className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                        >
                          <div className="flex items-center gap-3">
                            <Smartphone size={16} className="text-gray-400" />
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {device.device_name || 'Unknown device'}
                            </span>
                          </div>
                          <button
                            onClick={() => handleRemoveDevice(device.session_id)}
                            className="text-sm text-red-600 hover:text-red-700"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'language' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                Language & Region
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="zh">Chinese</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};