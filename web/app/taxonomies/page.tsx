'use client';

import { useEffect, useState } from 'react';
import { Tags } from 'lucide-react';
import { taxonomiesAPI } from '@/lib/api';

export default function TaxonomiesPage() {
  const [taxonomies, setTaxonomies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTaxonomies = async () => {
      try {
        const data = await taxonomiesAPI.list();
        setTaxonomies(data.taxonomies || []);
      } catch (err) {
        console.error('Failed to fetch taxonomies:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTaxonomies();
  }, []);

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Taxonomies</h1>
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <p className="text-gray-500 mb-4">{taxonomies.length} taxonomies loaded</p>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {taxonomies.map((tax) => (
            <div key={tax.id} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
              <div>
                <span className="font-medium">{tax.label_en}</span>
                {tax.label_hi && <span className="text-gray-500 ml-2">({tax.label_hi})</span>}
              </div>
              <span className="text-xs bg-gray-200 px-2 py-1 rounded">{tax.type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
