import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import {
  Calendar, Clock, CheckCircle2, XCircle, AlertCircle, Plus, User, Trash2, Pencil,
} from 'lucide-react';

function formatApptDate(value?: string | null): string {
  if (!value) return '';
  const d = new Date(value);
  return isNaN(d.getTime()) ? value : d.toLocaleString();
}

function toDateInputValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function toTimeInputValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function DoctorAppointmentsPage() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ patient_id: '', date: '', time: '', reason: '', is_follow_up: false });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [appts, pats] = await Promise.all([
        api.getDoctorAppointments(),
        api.getDoctorPatients(),
      ]);
      setAppointments(appts.appointments || []);
      setPatients(pats.patients || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const openNewForm = () => {
    setEditingId(null);
    setForm({ patient_id: '', date: '', time: '', reason: '', is_follow_up: false });
    setError('');
    setShowForm(true);
  };

  const openEditForm = (a: any) => {
    const d = a.appointment_date ? new Date(a.appointment_date) : new Date();
    setEditingId(a.id);
    setForm({
      patient_id: String(a.patient_id ?? ''),
      date: isNaN(d.getTime()) ? '' : toDateInputValue(d),
      time: isNaN(d.getTime()) ? '' : toTimeInputValue(d),
      reason: a.reason || '',
      is_follow_up: !!a.is_follow_up,
    });
    setError('');
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const schedule = async () => {
    setError('');
    if (!form.patient_id || !form.date) {
      setError('Please select a patient and a date.');
      return;
    }
    setSaving(true);
    try {
      const dateIso = form.time ? `${form.date}T${form.time}` : `${form.date}T09:00`;
      if (editingId) {
        await api.updateDoctorAppointment(editingId, {
          date: dateIso,
          reason: form.reason || 'Consultation',
          is_follow_up: form.is_follow_up,
        });
      } else {
        await api.createDoctorAppointment({
          patient_id: parseInt(form.patient_id),
          date: dateIso,
          reason: form.reason || 'Consultation',
          is_follow_up: form.is_follow_up,
        });
      }
      setShowForm(false);
      setEditingId(null);
      await loadData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const setStatus = async (id: number, status: string) => {
    try {
      await api.updateDoctorAppointment(id, { status });
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const cancel = async (id: number) => {
    try {
      await api.request(`/api/doctor/appointments/${id}`, { method: 'DELETE' });
      await loadData();
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (loading) return <LoadingSpinner message="Loading appointments..." />;

  const today = new Date().toDateString();
  const todays = appointments.filter(
    a => a.status === 'scheduled' && a.appointment_date && new Date(a.appointment_date).toDateString() === today
  );
  const upcoming = appointments.filter(a => {
    if (a.status !== 'scheduled') return false;
    const d = a.appointment_date ? new Date(a.appointment_date).toDateString() : '';
    return d !== today;
  });
  const past = appointments.filter(a => a.status !== 'scheduled');

  const statusIcon = (status: string) => {
    switch (status) {
      case 'scheduled': return <Clock className="text-blue-500" size={16} />;
      case 'completed': return <CheckCircle2 className="text-green-500" size={16} />;
      case 'cancelled': return <XCircle className="text-red-500" size={16} />;
      default: return <AlertCircle className="text-gray-400" size={16} />;
    }
  };

  const renderCard = (a: any, isToday: boolean) => (
    <div key={a.id} className={`card flex items-center gap-4 ${isToday ? 'border-primary-300 bg-primary-50/40' : ''}`}>
      {statusIcon(a.status)}
      <div className="flex-1">
        <p className="font-medium text-gray-900">{a.reason || 'Appointment'}</p>
        <p className="text-sm text-gray-600">{formatApptDate(a.appointment_date)}</p>
        <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
          <User size={12} /> {a.patient_name}
        </p>
      </div>
      {a.is_follow_up && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Follow-up</span>}
      {a.status === 'scheduled' && (
        <div className="flex items-center gap-1">
          <button
            onClick={() => setStatus(a.id, 'completed')}
            className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors"
            title="Mark completed"
          >
            <CheckCircle2 size={16} />
          </button>
          <button
            onClick={() => openEditForm(a)}
            className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
            title="Reschedule"
          >
            <Pencil size={16} />
          </button>
          <button
            onClick={() => cancel(a.id)}
            className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
            title="Cancel appointment"
          >
            <Trash2 size={16} />
          </button>
        </div>
      )}
      {a.status !== 'scheduled' && (
        <span className={`text-xs font-medium capitalize ${a.status === 'completed' ? 'text-green-600' : a.status === 'cancelled' ? 'text-red-500' : 'text-gray-500'}`}>{a.status}</span>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Calendar className="text-primary-500" size={22} /> Appointments
        </h2>
        <button onClick={() => (showForm && !editingId ? setShowForm(false) : openNewForm())} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Schedule Appointment
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">{error}</div>}

      {showForm && (
        <div className="card border-primary-200">
          <h3 className="font-bold text-gray-900 mb-4">{editingId ? 'Reschedule Appointment' : 'New Appointment'}</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Patient *</label>
              <select
                className="input-field mt-1 bg-gray-50"
                value={form.patient_id}
                disabled={!!editingId}
                onChange={e => setForm(f => ({ ...f, patient_id: e.target.value }))}
              >
                <option value="">Select patient...</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name}{p.village ? ` — ${p.village}` : ''}
                  </option>
                ))}
              </select>
              {editingId && <p className="text-xs text-gray-400 mt-1">Patient cannot be changed when rescheduling.</p>}
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Date *</label>
              <input
                type="date"
                className="input-field mt-1"
                min={editingId ? undefined : new Date().toISOString().slice(0, 10)}
                value={form.date}
                onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Time</label>
              <input
                type="time"
                className="input-field mt-1"
                value={form.time}
                onChange={e => setForm(f => ({ ...f, time: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Reason</label>
              <input
                type="text"
                className="input-field mt-1"
                placeholder="e.g., Follow-up, medication review..."
                value={form.reason}
                onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
              />
            </div>
          </div>
          <label className="flex items-center gap-2 mt-4 text-sm text-gray-700">
            <input
              type="checkbox"
              className="w-4 h-4 rounded"
              checked={form.is_follow_up}
              onChange={e => setForm(f => ({ ...f, is_follow_up: e.target.checked }))}
            />
            Mark as follow-up visit
          </label>
          <div className="flex gap-3 mt-4">
            <button onClick={schedule} className="btn-primary" disabled={saving}>
              {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Schedule'}
            </button>
            <button onClick={() => { setShowForm(false); setEditingId(null); setError(''); }} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {appointments.length === 0 ? (
        <EmptyState
          title="No appointments"
          description="You haven't scheduled any appointments yet. Click 'Schedule Appointment' to book one for a patient — it will appear on the patient's side immediately."
        />
      ) : (
        <>
          {todays.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Calendar size={16} className="text-primary-500" /> Today
              </h3>
              <div className="space-y-3">{todays.map(a => renderCard(a, true))}</div>
            </div>
          )}

          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Upcoming</h3>
            {upcoming.length === 0 ? (
              <p className="text-sm text-gray-500">No upcoming appointments.</p>
            ) : (
              <div className="space-y-3">{upcoming.map(a => renderCard(a, false))}</div>
            )}
          </div>

          {past.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Past</h3>
              <div className="space-y-3">{past.map(a => renderCard(a, false))}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
