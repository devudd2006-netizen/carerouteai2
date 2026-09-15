import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AlertBadge } from '../components/common/AlertBadge';
import { Users, Activity, AlertTriangle, Clock, ChevronRight } from 'lucide-react';

export function DoctorDashboard() {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDoctorPatients()
      .then(d => setPatients(d.patients || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading patient data..." />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Doctor Dashboard</h2>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <Users className="text-primary-500" size={24} />
            <div>
              <p className="text-xs text-gray-500">Total Patients</p>
              <p className="text-2xl font-bold">{patients.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-orange-500" size={24} />
            <div>
              <p className="text-xs text-gray-500">High Risk</p>
              <p className="text-2xl font-bold">{patients.filter(p => p.latest_risk_level === 'high' || p.latest_risk_level === 'emergency').length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Patient List */}
      <div className="card">
        <h3 className="font-bold text-gray-900 mb-4">Patients</h3>
        {patients.length === 0 ? (
          <p className="text-gray-500 text-sm py-4 text-center">No patients assigned yet.</p>
        ) : (
          <div className="divide-y">
            {patients.map(p => (
              <Link key={p.id} to={`/doctor/patients/${p.id}`} className="flex items-center gap-4 py-3 hover:bg-gray-50 px-2 rounded-lg transition-colors">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-700 font-semibold text-sm">{p.name?.charAt(0) || '?'}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{p.name}</p>
                  <p className="text-xs text-gray-500">{p.village}, {p.district} • Age: {p.age || 'N/A'}</p>
                </div>
                <div className="flex items-center gap-2">
                  {p.latest_risk_level && <AlertBadge level={p.latest_risk_level} size="sm" />}
                  {p.latest_checkin_date && <span className="text-xs text-gray-400">{new Date(p.latest_checkin_date).toLocaleDateString()}</span>}
                  <ChevronRight size={16} className="text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
