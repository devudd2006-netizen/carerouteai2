import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { AlertBadge } from '../components/common/AlertBadge';
import { Heart, Activity, Calendar, FileText, Pill, ClipboardList } from 'lucide-react';
import { Link } from 'react-router-dom';

export function HealthMemoryPage() {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTimeline()
      .then(d => setTimeline(d.timeline || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading your Health Memory..." />;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Heart className="text-red-500" size={22} /> Health Memory
          </h2>
          <p className="text-sm text-gray-500">Your complete longitudinal health profile</p>
        </div>
      </div>

      {timeline.length === 0 ? (
        <EmptyState
          title="No health records yet"
          description="Start your first health check-in to begin building your Health Memory."
          action={<Link to="/patient/checkin" className="btn-primary text-sm">Start Health Check</Link>}
        />
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />

          <div className="space-y-4">
            {timeline.map((entry, i) => (
              <div key={i} className="relative pl-12">
                <div className={`absolute left-3.5 w-3 h-3 rounded-full border-2 border-white ${
                  entry.type === 'health_checkin' ? 'bg-primary-500' : 'bg-healthcare-500'
                }`} />
                <div className="card">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {entry.type === 'health_checkin' ? <Activity size={16} className="text-primary-500" /> : <ClipboardList size={16} className="text-healthcare-500" />}
                      <span className="text-sm font-medium capitalize">{entry.type.replace('_', ' ')}</span>
                      {entry.data.risk_level && <AlertBadge level={entry.data.risk_level} size="sm" />}
                      {entry.data.urgency_level && <AlertBadge level={entry.data.urgency_level} size="sm" />}
                    </div>
                    <span className="text-xs text-gray-400">{entry.date ? new Date(entry.date).toLocaleDateString() : ''}</span>
                  </div>

                  {entry.type === 'health_checkin' && (
                    <div className="text-sm text-gray-600">
                      {entry.data.feeling_today && <p>Feeling: <span className="capitalize">{entry.data.feeling_today}</span></p>}
                      {entry.data.symptoms && entry.data.symptoms.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {entry.data.symptoms.map((s: string, j: number) => (
                            <span key={j} className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full">{s}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {entry.type === 'assessment' && (
                    <div className="text-sm text-gray-600 space-y-1">
                      {entry.data.possible_concerns && entry.data.possible_concerns.length > 0 && (
                        <div>
                          <p className="font-medium text-gray-700">Concerns:</p>
                          {entry.data.possible_concerns.map((c: any, j: number) => (
                            <p key={j} className="text-xs">• {c.concern || c}</p>
                          ))}
                        </div>
                      )}
                      {entry.data.diagnosis && <p>Diagnosis: {entry.data.diagnosis}</p>}
                      {entry.data.recommended_action && <p className="text-xs italic">Recommended: {entry.data.recommended_action}</p>}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
