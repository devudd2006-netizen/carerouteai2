import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { FileText, User, CheckCircle2, AlertCircle, Pill } from 'lucide-react';

export function PrescriptionsPage() {
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPrescriptions()
      .then(d => setPrescriptions(d.prescriptions || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading prescriptions..." />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
        <FileText className="text-blue-500" size={22} /> Prescriptions
      </h2>

      {prescriptions.length === 0 ? (
        <EmptyState
          title="No prescriptions"
          description="Prescriptions created by your doctor will appear here."
        />
      ) : (
        <div className="space-y-4">
          {prescriptions.map(p => (
            <div key={p.id} className="card">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-bold text-gray-900">{p.diagnosis || 'Prescription'}</h3>
                  <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                    <User size={12} /> {p.doctor_name || 'Doctor TBD'} · {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                  </p>
                </div>
                {p.is_confirmed ? (
                  <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex-shrink-0">
                    <CheckCircle2 size={12} /> Confirmed
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full flex-shrink-0">
                    <AlertCircle size={12} /> Needs confirmation
                  </span>
                )}
              </div>

              {p.items?.length > 0 && (
                <div className="mt-4 space-y-2">
                  {p.items.map((item: any) => (
                    <div key={item.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Pill size={14} className="text-purple-500 flex-shrink-0" />
                        <p className="text-sm font-semibold text-gray-900">{item.medicine_name}</p>
                        {item.needs_verification && (
                          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">Verify</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        {[item.dosage, item.frequency, item.duration].filter(Boolean).join(' · ')}
                      </p>
                      {item.instructions && <p className="text-xs text-gray-500 italic mt-1">{item.instructions}</p>}
                    </div>
                  ))}
                </div>
              )}

              {p.notes && <p className="text-sm text-gray-600 mt-3 border-t pt-3">{p.notes}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
