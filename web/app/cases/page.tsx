'use client';

import { useEffect, useState } from 'react';
import { Folder, MapPin, Calendar, User } from 'lucide-react';
import { casesAPI } from '@/lib/api';
import { format } from 'date-fns';

interface Case {
  id: string;
  title: string;
  summary: string;
  status: string;
  issue_type: string;
  location_text: string;
  created_at: string;
  user_id: string;
}

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const params = filter ? { status: filter } : {};
        const data = await casesAPI.list(params);
        setCases(data.cases || []);
      } catch (err) {
        console.error('Failed to fetch cases:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCases();
  }, [filter]);

  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    submitted: 'bg-blue-100 text-blue-800',
    moderation: 'bg-yellow-100 text-yellow-800',
    routed: 'bg-purple-100 text-purple-800',
    officer_accepted: 'bg-indigo-100 text-indigo-800',
    in_progress: 'bg-orange-100 text-orange-800',
    resolved: 'bg-green-100 text-green-800',
    verified: 'bg-teal-100 text-teal-800',
    closed: 'bg-gray-100 text-gray-800',
    rejected: 'bg-red-100 text-red-800',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading cases...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Cases Management</h1>
          <p className="text-gray-500 mt-1">{cases.length} total cases</p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">All Statuses</option>
          <option value="submitted">Submitted</option>
          <option value="routed">Routed</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {/* Cases List */}
      {cases.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <Folder className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No cases found</h3>
          <p className="text-gray-500">Cases will appear here when citizens submit grievances.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {cases.map((caseItem) => (
            <div
              key={caseItem.id}
              className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {caseItem.title || 'Untitled Case'}
                  </h3>
                  {caseItem.summary && (
                    <p className="text-gray-600 text-sm mb-3">{caseItem.summary}</p>
                  )}
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[caseItem.status] || 'bg-gray-100 text-gray-800'}`}>
                  {caseItem.status.replace(/_/g, ' ').toUpperCase()}
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <Folder className="w-4 h-4" />
                  <span>ID: {caseItem.id.substring(0, 8)}...</span>
                </div>
                {caseItem.issue_type && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <span className="font-medium">Type:</span>
                    <span>{caseItem.issue_type}</span>
                  </div>
                )}
                {caseItem.location_text && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <MapPin className="w-4 h-4" />
                    <span>{caseItem.location_text}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="w-4 h-4" />
                  <span>{format(new Date(caseItem.created_at), 'MMM d, yyyy')}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
