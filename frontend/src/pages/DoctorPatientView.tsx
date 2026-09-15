import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AlertBadge } from '../components/common/AlertBadge';
import { ArrowLeft, User, Activity, FileText, Pill, Calendar, Stethoscope } from 'lucide-react';

export function DoctorPatientView() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [consultation, setConsultation] = useState({ notes: '', diagnosis: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      api.getDoctorPatient(parseInt(id))
        .then(d => setData(d))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [id]);

  const saveConsultation = async () => {
    if (!consultation.diagnosis && !consultation.notes) return;
    setSaving(true);
    try {
      await api.addConsultation({
        patient_id: parseInt(id!),
        notes: consultation.notes,
        diagnosis: consultation.diagnosis,
      });
      alert('Consultation notes saved');
      setConsultation({ notes: '', diagnosis: '' });
    } catch (e: any) { alert(e.message); }
    finally { setSaving(false); }
  };

  if (loading) return <LoadingSpinner message="Loading patient data..." />;
  if (!data) return <p className="text-center py-12 text-gray-500">Patient not found</p>;

  const { profile, checkins, assessments, care_plans, documents } = data;

  return (
    <div className="space-y-6">
      <Link to="/doctor" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} /> Back to Dashboard
      </Link>

      {/* Patient Header */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-primary-700 font-bold text-xl">{profile.name?.charAt(0) || '?'}</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{profile.name}</h2>
            <p className="text-sm text-gray-600">Age: {profile.age || 'N/A'} • Gender: {profile.gender || 'N/A'} • Blood: {profile.blood_group || 'N/A'}</p>
            <p className="text-sm text-gray-500">{profile.village}, {profile.district}</p>
          </div>
        </div>
        {profile.allergies && <div className="mt-3 p-2 bg-yellow-50 rounded text-sm text-yellow-700">⚠️ Allergies: {profile.allergies}</div>}
        {profile.chronic_conditions && <div className="mt-2 p-2 bg-orange-50 rounded text-sm text-orange-700">📋 Chronic conditions: {profile.chronic_conditions}</div>}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Check-ins */}
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2"><Activity size={16} /> Recent Check-ins</h3>
          {checkins?.length > 0 ? (
            <div className="space-y-2">
              {checkins.slice(0, 5).map((c: any) => (
                <div key={c.id} className="p-2 bg-gray-50 rounded text-sm">
                  <div className="flex items-center gap-2">
                    <AlertBadge level={c.risk_level || 'low'} size="sm" />
                    <span className="text-xs text-gray-400">{c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</span>
                  </div>
                  {c.symptoms && <p className="text-xs text-gray-600 mt-1">{Array.isArray(c.symptoms) ? c.symptoms.join(', ') : ''}</p>}
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-gray-500">No check-ins yet.</p>}
        </div>

        {/* Assessments */}
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2"><Stethoscope size={16} /> Assessments</h3>
          {assessments?.length > 0 ? (
            <div className="space-y-2">
              {assessments.slice(0, 5).map((a: any) => (
                <div key={a.id} className="p-2 bg-gray-50 rounded text-sm">
                  <div className="flex items-center gap-2">
                    <AlertBadge level={a.urgency_level || 'low'} size="sm" />
                    <span className="text-xs text-gray-400">{a.created_at ? new Date(a.created_at).toLocaleDateString() : ''}</span>
                  </div>
                  {a.diagnosis && <p className="text-xs font-medium mt-1">Diagnosis: {a.diagnosis}</p>}
                  {a.doctor_notes && <p className="text-xs text-gray-600 mt-1">Notes: {a.doctor_notes}</p>}
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-gray-500">No assessments yet.</p>}
        </div>
      </div>

      {/* Doctor Assessment Form */}
      <div className="card border-healthcare-200">
        <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Stethoscope size={16} /> Doctor Assessment
        </h3>
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700">Diagnosis</label>
            <input className="input-field mt-1" value={consultation.diagnosis} onChange={e => setConsultation(c => ({ ...c, diagnosis: e.target.value }))} placeholder="Enter diagnosis..." />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Consultation Notes</label>
            <textarea className="input-field mt-1" rows={4} value={consultation.notes} onChange={e => setConsultation(c => ({ ...c, notes: e.target.value }))} placeholder="Enter clinical notes, observations, and recommendations..." />
          </div>
          <button onClick={saveConsultation} className="btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Assessment'}
          </button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
        ℹ️ Doctor Assessment is clearly separated from AI Preliminary Screening. Both are displayed distinctly to maintain clarity.
      </div>
    </div>
  );
}
