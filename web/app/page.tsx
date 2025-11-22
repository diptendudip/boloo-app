'use client';

import { useEffect, useState } from 'react';
import { Folder, Users, Building2, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { adminAPI } from '@/lib/api';
import Link from 'next/link';

interface Stats {
  total_cases: number;
  total_users: number;
  total_entities: number;
  cases_by_status: Record<string, number>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await adminAPI.getStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    submitted: 'bg-blue-100 text-blue-800',
    routed: 'bg-yellow-100 text-yellow-800',
    in_progress: 'bg-purple-100 text-purple-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Welcome to Boloo Admin Console</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Total Cases */}
        <Link href="/cases">
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">Total Cases</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_cases || 0}</p>
              </div>
              <div className="p-3 bg-primary-100 rounded-lg">
                <Folder className="w-8 h-8 text-primary-600" />
              </div>
            </div>
          </div>
        </Link>

        {/* Total Users */}
        <Link href="/users">
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">Total Users</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_users || 0}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <Users className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>
        </Link>

        {/* Total Entities */}
        <Link href="/entities">
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">Government Entities</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_entities || 0}</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <Building2 className="w-8 h-8 text-purple-600" />
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* Cases by Status */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Cases by Status</h2>
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          {stats?.cases_by_status && Object.keys(stats.cases_by_status).length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {Object.entries(stats.cases_by_status).map(([status, count]) => (
                <div key={status} className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className={`inline-flex px-3 py-1 rounded-full text-xs font-medium mb-2 ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
                    {status.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No cases yet</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/monitoring">
            <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">System Monitoring</h3>
                  <p className="text-sm text-gray-500">View real-time system health</p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/cases">
            <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Folder className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">View All Cases</h3>
                  <p className="text-sm text-gray-500">Manage citizen grievances</p>
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* System Info */}
      <div className="bg-primary-50 border border-primary-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-primary-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-primary-900 mb-2">Phase 1 MVP Active</h3>
            <p className="text-sm text-primary-800 mb-2">
              Core functionality is operational. Email OTPs are sent to <code className="bg-white px-2 py-0.5 rounded">diptendudip@gmail.com</code> for Phase 1 testing.
            </p>
            <p className="text-sm text-primary-800">
              For full feature list and roadmap, see <code className="bg-white px-2 py-0.5 rounded">docs/DEVELOPMENT_PHASES.md</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
