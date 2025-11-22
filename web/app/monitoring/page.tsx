'use client';

import { useEffect, useState } from 'react';
import { RefreshCw, Server, Database, HardDrive, Cloud, Mail, Cpu } from 'lucide-react';
import StatusIndicator, { StatusType } from '@/components/StatusIndicator';
import { monitoringAPI } from '@/lib/api';

interface HealthData {
  overall_status: string;
  timestamp: string;
  infrastructure: {
    database: { status: StatusType; message: string };
    redis: { status: StatusType; message: string };
    storage: { status: StatusType; message: string };
  };
  external_services: {
    azure_speech: { status: StatusType; message: string };
    claude_api: { status: StatusType; message: string };
    smtp: { status: StatusType; message: string };
  };
  api_endpoints: Array<{ path: string; name: string }>;
  version: string;
}

export default function MonitoringPage() {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [countdown, setCountdown] = useState(60);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await monitoringAPI.health();
      setHealthData(data);
      setLastUpdated(new Date());
      setCountdown(60);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch health status');
      console.error('Health check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 60 seconds
  useEffect(() => {
    fetchHealth();

    const refreshInterval = setInterval(() => {
      fetchHealth();
    }, 60000); // 60 seconds

    return () => clearInterval(refreshInterval);
  }, []);

  // Countdown timer
  useEffect(() => {
    const countdownInterval = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 60));
    }, 1000);

    return () => clearInterval(countdownInterval);
  }, [lastUpdated]);

  const handleManualRefresh = () => {
    fetchHealth();
  };

  if (loading && !healthData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading system status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Operational Monitoring</h1>
          <p className="text-gray-500 mt-1">Real-time system health and endpoint status</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600">
            Next refresh in <span className="font-mono font-bold">{countdown}s</span>
          </div>
          <button
            onClick={handleManualRefresh}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Now
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">Error: {error}</p>
        </div>
      )}

      {/* Overall Status Card */}
      {healthData && (
        <div className="mb-6 p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Overall System Status</h2>
              <StatusIndicator
                status={healthData.overall_status as StatusType}
                size="lg"
              />
            </div>
            <div className="text-right text-sm text-gray-500">
              <div>Version: {healthData.version}</div>
              <div>Last updated: {lastUpdated.toLocaleTimeString()}</div>
            </div>
          </div>
        </div>
      )}

      {/* Infrastructure Status */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          Infrastructure
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Database */}
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <Database className="w-6 h-6 text-primary-600" />
              <h3 className="font-semibold text-gray-900">PostgreSQL</h3>
            </div>
            {healthData && (
              <>
                <StatusIndicator
                  status={healthData.infrastructure.database.status}
                  message={healthData.infrastructure.database.message}
                />
                <p className="mt-2 text-xs text-gray-500">{healthData.infrastructure.database.message}</p>
              </>
            )}
          </div>

          {/* Redis */}
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <Cpu className="w-6 h-6 text-primary-600" />
              <h3 className="font-semibold text-gray-900">Redis</h3>
            </div>
            {healthData && (
              <>
                <StatusIndicator
                  status={healthData.infrastructure.redis.status}
                  message={healthData.infrastructure.redis.message}
                />
                <p className="mt-2 text-xs text-gray-500">{healthData.infrastructure.redis.message}</p>
              </>
            )}
          </div>

          {/* Storage (MinIO) */}
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <HardDrive className="w-6 h-6 text-primary-600" />
              <h3 className="font-semibold text-gray-900">Object Storage</h3>
            </div>
            {healthData && (
              <>
                <StatusIndicator
                  status={healthData.infrastructure.storage.status}
                  message={healthData.infrastructure.storage.message}
                />
                <p className="mt-2 text-xs text-gray-500">{healthData.infrastructure.storage.message}</p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* External Services */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Cloud className="w-5 h-5" />
          External Services
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Azure Speech */}
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <Cloud className="w-6 h-6 text-primary-600" />
              <h3 className="font-semibold text-gray-900">Azure Speech</h3>
            </div>
            {healthData && (
              <>
                <StatusIndicator
                  status={healthData.external_services.azure_speech.status}
                  message={healthData.external_services.azure_speech.message}
                />
                <p className="mt-2 text-xs text-gray-500">{healthData.external_services.azure_speech.message}</p>
              </>
            )}
          </div>

          {/* Claude API */}
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <Cpu className="w-6 h-6 text-primary-600" />
              <h3 className="font-semibold text-gray-900">Claude API</h3>
            </div>
            {healthData && (
              <>
                <StatusIndicator
                  status={healthData.external_services.claude_api.status}
                  message={healthData.external_services.claude_api.message}
                />
                <p className="mt-2 text-xs text-gray-500">{healthData.external_services.claude_api.message}</p>
              </>
            )}
          </div>

          {/* SMTP */}
          <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <Mail className="w-6 h-6 text-primary-600" />
              <h3 className="font-semibold text-gray-900">SMTP</h3>
            </div>
            {healthData && (
              <>
                <StatusIndicator
                  status={healthData.external_services.smtp.status}
                  message={healthData.external_services.smtp.message}
                />
                <p className="mt-2 text-xs text-gray-500">{healthData.external_services.smtp.message}</p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* API Endpoints */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          API Endpoints
        </h2>
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Endpoint
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {healthData?.api_endpoints.map((endpoint) => (
                <tr key={endpoint.path} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {endpoint.path}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {endpoint.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusIndicator status="healthy" size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
