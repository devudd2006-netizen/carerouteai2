import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { BarChart3, Users, Building2, AlertTriangle, Clock, MapPin, Tent, Shield } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function AdminDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAdminDashboard()
      .then(d => setStats(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading admin dashboard..." />;

  const statCards = [
    { icon: Users, label: 'Total Patients', value: stats?.total_patients || 0, color: 'primary' },
    { icon: Shield, label: 'Active Doctors', value: stats?.active_doctors || 0, color: 'healthcare' },
    { icon: Building2, label: 'Healthcare Facilities', value: stats?.healthcare_facilities || 0, color: 'blue' },
    { icon: AlertTriangle, label: 'High-Risk Alerts (7d)', value: stats?.high_risk_alerts || 0, color: 'orange' },
    { icon: Clock, label: 'Pending Follow-ups', value: stats?.pending_followups || 0, color: 'purple' },
    { icon: MapPin, label: 'High-Priority Communities', value: stats?.high_priority_communities || 0, color: 'red' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Admin Dashboard</h2>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map(({ icon: Icon, label, value, color }, i) => (
          <div key={i} className="card">
            <Icon className={`text-${color}-500 mb-2`} size={24} />
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* System Info */}
      <div className="card">
        <h3 className="font-bold text-gray-900 mb-4">System Overview</h3>
        <div className="grid sm:grid-cols-2 gap-4 text-sm">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-gray-500">Total Users</p>
            <p className="text-xl font-bold">{stats?.total_users || 0}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-gray-500">Recent Sign-ups (7d)</p>
            <p className="text-xl font-bold">{stats?.recent_signups || 0}</p>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>CareRoute AI</strong> — Admin dashboard for managing users, facilities, and monitoring system health.
      </div>
    </div>
  );
}
