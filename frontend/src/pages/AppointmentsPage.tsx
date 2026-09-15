import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Calendar, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

export function AppointmentsPage() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const data = await api.getAppointments();
      setAppointments(data.appointments || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  if (loading) return <LoadingSpinner message="Loading appointments..." />;

  const upcoming = appointments.filter(a => a.status === 'scheduled');
  const completed = appointments.filter(a => a.status === 'completed');

  const statusIcon = (status: string) => {
    switch (status) {
      case 'scheduled': return <Clock className="text-blue-500" size={16} />;
      case 'completed': return <CheckCircle2 className="text-green-500" size={16} />;
      case 'cancelled': return <XCircle className="text-red-500" size={16} />;
      default: return <AlertCircle className="text-gray-400" size={16} />;
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
        <Calendar className="text-orange-500" size={22} /> Appointments
      </h2>

      {appointments.length === 0 ? (
        <EmptyState title="No appointments" description="No appointments scheduled yet." />
      ) : (
        <>
          {/* Upcoming */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Upcoming</h3>
            {upcoming.length === 0 ? (
              <p className="text-sm text-gray-500">No upcoming appointments.</p>
            ) : (
              <div className="space-y-3">
                {upcoming.map(a => (
                  <div key={a.id} className="card flex items-center gap-4">
                    {statusIcon(a.status)}
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{a.reason || 'Appointment'}</p>
                      <p className="text-sm text-gray-600">{new Date(a.appointment_date).toLocaleString()}</p>
                      {a.is_follow_up && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Follow-up</span>}
                    </div>
                    <span className="text-xs text-blue-600 font-medium capitalize">{a.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Completed */}
          {completed.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Completed</h3>
              <div className="space-y-3">
                {completed.map(a => (
                  <div key={a.id} className="card flex items-center gap-4 opacity-75">
                    {statusIcon(a.status)}
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{a.reason || 'Appointment'}</p>
                      <p className="text-sm text-gray-600">{new Date(a.appointment_date).toLocaleString()}</p>
                    </div>
                    <span className="text-xs text-green-600 font-medium">Completed</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
