'use client';

import { useEffect, useState } from 'react';
import { Building2, MapPin, Mail, Phone } from 'lucide-react';
import { entitiesAPI } from '@/lib/api';

interface Entity {
  id: string;
  name: string;
  type: string;
  contact_email: string;
  contact_phone: string;
  is_active: boolean;
}

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');

  useEffect(() => {
    const fetchEntities = async () => {
      try {
        const data = await entitiesAPI.list();
        setEntities(data.entities || []);
      } catch (err) {
        console.error('Failed to fetch entities:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, []);

  const filteredEntities = filter
    ? entities.filter((e) => e.type === filter)
    : entities;

  const typeColors: Record<string, string> = {
    district: 'bg-blue-100 text-blue-800',
    block: 'bg-green-100 text-green-800',
    gp: 'bg-purple-100 text-purple-800',
    dept: 'bg-orange-100 text-orange-800',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading entities...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Government Entities</h1>
          <p className="text-gray-500 mt-1">{filteredEntities.length} entities</p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">All Types</option>
          <option value="district">Districts</option>
          <option value="block">Blocks</option>
          <option value="gp">Gram Panchayats</option>
          <option value="dept">Departments</option>
        </select>
      </div>

      {/* Entities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEntities.map((entity) => (
          <div
            key={entity.id}
            className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <Building2 className="w-5 h-5 text-primary-600" />
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${typeColors[entity.type]}`}>
                  {entity.type.toUpperCase()}
                </div>
              </div>
            </div>

            <h3 className="font-semibold text-gray-900 mb-3">{entity.name}</h3>

            <div className="space-y-2 text-sm">
              {entity.contact_email && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Mail className="w-4 h-4" />
                  <span className="truncate">{entity.contact_email}</span>
                </div>
              )}
              {entity.contact_phone && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone className="w-4 h-4" />
                  <span>{entity.contact_phone}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
