import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Users, 
  Activity, 
  Database, 
  Server, 
  Settings, 
  Shield, 
  Cog, 
  AlertCircle,
  CheckCircle,
  Clock,
  Search,
  FileText
} from 'lucide-react';

// Types
interface SystemStats {
  totalUsers: number;
  totalDocuments: number;
  searchQueries: number;
  activeSessions: number;
  databaseSize: string;
  cacheHitRate: number;
  avgResponseTime: number;
  errorRate: number;
}

interface SystemStatus {
  postgres: 'online' | 'degraded' | 'offline';
  redis: 'online' | 'degraded' | 'offline';
  elasticsearch: 'online' | 'degraded' | 'offline';
  rabbitmq: 'online' | 'degraded' | 'offline';
  kafka: 'online' | 'degraded' | 'offline';
}

// Mock data (replace with actual API calls)
const initialStats: SystemStats = {
  totalUsers: 1247,
  totalDocuments: 58342,
  searchQueries: 15243,
  activeSessions: 234,
  databaseSize: '2.4GB',
  cacheHitRate: 87.5,
  avgResponseTime: 125,
  errorRate: 0.02
};

const initialStatus: SystemStatus = {
  postgres: 'online',
  redis: 'online',
  elasticsearch: 'online',
  rabbitmq: 'online',
  kafka: 'online'
};

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats>(initialStats);
  const [status, setStatus] = useState<SystemStatus>(initialStatus);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-500';
      case 'degraded': return 'text-yellow-500';
      case 'offline': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-5 h-5" />;
      case 'degraded': return <AlertCircle className="w-5 h-5" />;
      case 'offline': return <AlertCircle className="w-5 h-5" />;
      default: return <AlertCircle className="w-5 h-5" />;
    }
  };

  const statsCards = [
    { title: 'Total Users', value: stats.totalUsers.toLocaleString(), icon: Users, color: 'bg-blue-500' },
    { title: 'Total Documents', value: stats.totalDocuments.toLocaleString(), icon: FileText, color: 'bg-green-500' },
    { title: 'Search Queries', value: stats.searchQueries.toLocaleString(), icon: Search, color: 'bg-purple-500' },
    { title: 'Active Sessions', value: stats.activeSessions.toLocaleString(), icon: Activity, color: 'bg-orange-500' },
    { title: 'Database Size', value: stats.databaseSize, icon: Database, color: 'bg-indigo-500' },
    { title: 'Cache Hit Rate', value: `${stats.cacheHitRate}%`, icon: Server, color: 'bg-teal-500' },
    { title: 'Avg Response Time', value: `${stats.avgResponseTime}ms`, icon: Clock, color: 'bg-pink-500' },
    { title: 'Error Rate', value: `${(stats.errorRate * 100).toFixed(2)}%`, icon: AlertCircle, color: 'bg-red-500' },
  ];

  const services = [
    { name: 'PostgreSQL', status: status.postgres, icon: Database },
    { name: 'Redis', status: status.redis, icon: Server },
    { name: 'Elasticsearch', status: status.elasticsearch, icon: Search },
    { name: 'RabbitMQ', status: status.rabbitmq, icon: AlertCircle },
    { name: 'Kafka', status: status.kafka, icon: AlertCircle },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-indigo-600" />
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">Admin Dashboard</span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="p-2 rounded-full text-gray-400 hover:text-gray-500">
                <Settings className="h-6 w-6" />
              </button>
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center">
                  <span className="text-white font-bold">AD</span>
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Admin</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['overview', 'users', 'documents', 'system', 'logs', 'settings'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === tab
                    ? 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {statsCards.map((stat, index) => (
                    <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                            {stat.title}
                          </p>
                          <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">
                            {stat.value}
                          </p>
                        </div>
                        <div className={`p-3 rounded-lg ${stat.color} bg-opacity-10`}>
                          <stat.icon className={`h-6 w-6 ${stat.color.replace('bg-', 'text-')}`} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* System Status */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">System Status</h3>
                  </div>
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {services.map((service, index) => (
                      <div key={index} className="px-6 py-4 flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <service.icon className={`w-5 h-5 ${getStatusColor(service.status)}`} />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {service.name}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(service.status)}
                          <span className={`text-sm font-medium ${getStatusColor(service.status)}`}>
                            {service.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">Recent Activity</h3>
                  </div>
                  <div className="px-6 py-4 space-y-4">
                    {[
                      { user: 'John Doe', action: 'Indexed 500 documents', time: '2 minutes ago' },
                      { user: 'Jane Smith', action: 'Search: "machine learning"', time: '5 minutes ago' },
                      { user: 'System', action: 'Daily backup completed', time: '1 hour ago' },
                      { user: 'Admin', action: 'Updated system settings', time: '2 hours ago' },
                    ].map((activity, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                              {activity.user.charAt(0)}
                            </span>
                          </div>
                          <div>
                            <p className="text-sm text-gray-900 dark:text-white">
                              <span className="font-medium">{activity.user}</span> {activity.action}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {activity.time}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">User Management</h3>
                </div>
                <div className="px-6 py-4">
                  <p className="text-gray-500 dark:text-gray-400">User management dashboard coming soon...</p>
                </div>
              </div>
            )}

            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">Document Management</h3>
                </div>
                <div className="px-6 py-4">
                  <p className="text-gray-500 dark:text-gray-400">Document management dashboard coming soon...</p>
                </div>
              </div>
            )}

            {/* System Tab */}
            {activeTab === 'system' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">System Configuration</h3>
                </div>
                <div className="px-6 py-4 space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Search Configuration</h4>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input type="checkbox" className="rounded text-indigo-600" defaultChecked />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable hybrid search</span>
                      </label>
                      <label className="flex items-center">
                        <input type="checkbox" className="rounded text-indigo-600" defaultChecked />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable semantic search</span>
                      </label>
                      <label className="flex items-center">
                        <input type="checkbox" className="rounded text-indigo-600" />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable AI enhancements</span>
                      </label>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">System Settings</h4>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input type="checkbox" className="rounded text-indigo-600" defaultChecked />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable caching</span>
                      </label>
                      <label className="flex items-center">
                        <input type="checkbox" className="rounded text-indigo-600" />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable rate limiting</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Logs Tab */}
            {activeTab === 'logs' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">System Logs</h3>
                </div>
                <div className="px-6 py-4">
                  <p className="text-gray-500 dark:text-gray-400">System logs dashboard coming soon...</p>
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">Settings</h3>
                </div>
                <div className="px-6 py-4">
                  <p className="text-gray-500 dark:text-gray-400">Settings dashboard coming soon...</p>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
