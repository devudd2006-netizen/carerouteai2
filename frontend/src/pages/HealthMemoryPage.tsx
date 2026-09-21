import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { AlertBadge } from '../components/common/AlertBadge';
import { Heart, Activity, Calendar, FileText, Pill, ClipboardList, TrendingUp, Stethoscope } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts';

interface TrendSeriesPoint {
  date: string | null;
  feeling_today: string | null;
  risk_level: string;
  symptom_count: number;
  sleep_quality: number | null;
  stress_level: number | null;
  pain_severity: number | null;
}

interface TrendsData {
  series: TrendSeriesPoint[];
  top_symptoms: { symptom: string; count: number }[];
  feeling_counts: Record<string, number>;
  risk_counts: Record<string, number>;
  total_checkins: number;
}

export function HealthMemoryPage() {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [trends, setTrends] = useState<TrendsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getTimeline().then(d => setTimeline(d.timeline || [])).catch(() => {}),
      api.getTrends().then(d => setTrends(d)).catch(() => {}),
    ]).finally(() => setLoading(false));
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
        <div className="space-y-6">
          {/* Health Trends */}
          {trends && trends.total_checkins > 0 && (
            <div className="card">
              <h3 className="font-bold text-gray-900 mb-1 flex items-center gap-2">
                <TrendingUp className="text-primary-500" size={18} /> Health Trends
              </h3>
              <p className="text-xs text-gray-500 mb-4">Last {trends.total_checkins} check-ins</p>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Symptoms per check-in</p>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={trends.series}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v: string) => (v ? v.slice(5) : '')} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 10 }} width={24} />
                      <Tooltip />
                      <Bar dataKey="symptom_count" name="Symptoms" fill="#16a34a" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Sleep & stress (1–5)</p>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={trends.series}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v: string) => (v ? v.slice(5) : '')} />
                      <YAxis domain={[0, 5]} tick={{ fontSize: 10 }} width={24} />
                      <Tooltip />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Line type="monotone" dataKey="sleep_quality" name="Sleep" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="stress_level" name="Stress" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              {trends.top_symptoms.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Most reported symptoms</p>
                  <div className="flex flex-wrap gap-2">
                    {trends.top_symptoms.map(({ symptom, count }) => (
                      <span key={symptom} className="bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full">
                        {symptom.replace('_', ' ')} · {count}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

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
                    <div className={`text-sm space-y-1 ${entry.data.is_doctor_consultation ? 'bg-healthcare-50 -m-3 p-3 rounded-lg border border-healthcare-100' : 'text-gray-600'}`}>
                      {entry.data.is_doctor_consultation && (
                        <p className="font-medium text-healthcare-700 flex items-center gap-1">
                          <Stethoscope size={14} /> Doctor Consultation{entry.data.doctor_name ? ` — ${entry.data.doctor_name}` : ''}
                        </p>
                      )}
                      {entry.data.diagnosis && <p><span className="font-medium">Diagnosis:</span> {entry.data.diagnosis}</p>}
                      {entry.data.doctor_notes && <p className="text-gray-700">{entry.data.doctor_notes}</p>}
                      {entry.data.possible_concerns && entry.data.possible_concerns.length > 0 && !entry.data.is_doctor_consultation && (
                        <div>
                          <p className="font-medium text-gray-700">Concerns:</p>
                          {entry.data.possible_concerns.map((c: any, j: number) => (
                            <p key={j} className="text-xs">• {c.concern || c}</p>
                          ))}
                        </div>
                      )}
                      {entry.data.recommended_action && !entry.data.is_doctor_consultation && (
                        <p className="text-xs italic">Recommended: {entry.data.recommended_action}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        </div>
      )}
    </div>
  );
}
