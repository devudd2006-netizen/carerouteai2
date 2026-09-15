import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AlertBadge } from '../components/common/AlertBadge';
import {
  Activity, Heart, MapPin, Pill, FileText, AlertTriangle,
  Calendar, ClipboardList, ArrowRight, Clock
} from 'lucide-react';

export function PatientDashboard() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [checkins, setCheckins] = useState<any[]>([]);
  const [carePlans, setCarePlans] = useState<any[]>([]);
  const [medications, setMedications] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [p, c, cp, m] = await Promise.all([
        api.getProfile().catch(() => null),
        api.getCheckins().catch(() => []),
        api.getCarePlans().catch(() => ({ care_plans: [] })),
        api.getMedications().catch(() => ({ medications: [] })),
      ]);
      setProfile(p);
      setCheckins(Array.isArray(c) ? c : []);
      setCarePlans(cp?.care_plans || []);
      setMedications(m);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading your dashboard..." />;

  const greeting = getGreeting();
  const firstName = user?.full_name?.split(' ')[0] || 'there';
  const latestCheckin = checkins[0];

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-6 text-white">
        <h2 className="text-2xl font-bold">{greeting}, {firstName} 👋</h2>
        <p className="text-primary-100 mt-1">Here's your health overview for today.</p>
        {profile?.village && (
          <p className="text-primary-200 text-sm mt-2">📍 {profile.village}, {profile.district || ''}</p>
        )}
      </div>

      {/* Quick Status Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <Activity className="text-primary-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Health Status</p>
              <p className="font-semibold text-sm">
                {latestCheckin ? (
                  <span className="flex items-center gap-1">
                    <AlertBadge level={latestCheckin.ai_risk_level || 'low'} size="sm" />
                  </span>
                ) : 'No check-in yet'}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <ClipboardList className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Check-ins</p>
              <p className="font-semibold">{checkins.length} total</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Pill className="text-purple-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Medications</p>
              <p className="font-semibold">{medications?.medications?.length || 0} active</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <Calendar className="text-orange-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Care Plans</p>
              <p className="font-semibold">{carePlans.length} active</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { to: '/patient/checkin', icon: Activity, label: 'Health Check', color: 'primary' },
          { to: '/patient/health-memory', icon: Heart, label: 'Health Memory', color: 'red' },
          { to: '/patient/care-route', icon: MapPin, label: 'Find Care', color: 'healthcare' },
          { to: '/patient/medications', icon: Pill, label: 'My Medicines', color: 'purple' },
          { to: '/patient/documents', icon: FileText, label: 'Upload Report', color: 'blue' },
          { to: '/patient/emergency', icon: AlertTriangle, label: 'Emergency', color: 'danger' },
        ].map(({ to, icon: Icon, label, color }) => (
          <Link key={to} to={to} className={`card hover:shadow-md transition-all text-center py-4 border-${color}-100 hover:border-${color}-300`}>
            <Icon className={`mx-auto mb-2 text-${color}-500`} size={24} />
            <span className="text-sm font-medium text-gray-700">{label}</span>
          </Link>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Latest Check-in */}
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-4">Today's Health Check-in</h3>
          {latestCheckin ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm text-gray-500"><Clock size={14} className="inline" /> {new Date(latestCheckin.created_at).toLocaleDateString()}</span>
                <AlertBadge level={latestCheckin.ai_risk_level || 'low'} size="sm" />
              </div>
              <p className="text-sm text-gray-600">
                Feeling: {latestCheckin.feeling_today || 'Not specified'}
              </p>
              {latestCheckin.symptoms && latestCheckin.symptoms.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {latestCheckin.symptoms.map((s: string, i: number) => (
                    <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">{s}</span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-gray-500 text-sm mb-3">No health check-in yet today.</p>
              <Link to="/patient/checkin" className="btn-primary text-sm inline-flex items-center gap-2">
                Start Health Check <ArrowRight size={16} />
              </Link>
            </div>
          )}
        </div>

        {/* Current Care Plan */}
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-4">Current Care Plan</h3>
          {carePlans.length > 0 ? (
            <div>
              <p className="font-medium text-gray-800">{carePlans[0].title}</p>
              {carePlans[0].doctor_instructions && (
                <p className="text-sm text-gray-600 mt-2">{carePlans[0].doctor_instructions}</p>
              )}
              {carePlans[0].follow_up_date && (
                <p className="text-sm text-primary-600 mt-2 font-medium">📅 Follow-up: {carePlans[0].follow_up_date}</p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm py-4">No active care plans.</p>
          )}
        </div>
      </div>

      {/* Recent Health Timeline */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-gray-900">Recent Health Timeline</h3>
          <Link to="/patient/health-memory" className="text-sm text-primary-600 hover:underline">View All</Link>
        </div>
        {checkins.length > 0 ? (
          <div className="space-y-3">
            {checkins.slice(0, 5).map((c, i) => (
              <div key={c.id || i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className={`w-3 h-3 rounded-full mt-1 ${
                  c.ai_risk_level === 'emergency' ? 'bg-red-500' :
                  c.ai_risk_level === 'high' ? 'bg-orange-500' :
                  c.ai_risk_level === 'moderate' ? 'bg-yellow-500' : 'bg-green-500'
                }`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Health Check-in</span>
                    <AlertBadge level={c.ai_risk_level || 'low'} size="sm" />
                  </div>
                  <p className="text-xs text-gray-500">{c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</p>
                  {c.symptoms && <p className="text-xs text-gray-600 mt-1">{c.symptoms.join(', ')}</p>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm py-4 text-center">No health records yet. Start your first health check-in!</p>
        )}
      </div>
    </div>
  );
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}
