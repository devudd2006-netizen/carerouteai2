import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Pill, Check, X, Minus, Plus, Trash2, Stethoscope, User, Info } from 'lucide-react';

type Medication = {
  id: number;
  medicine_name: string;
  dosage: string | null;
  frequency: string | null;
  time_of_day: string | null;
  instructions?: string | null;
  source?: string;
};

export function MedicationsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    medicine_name: '', dosage: '', frequency: '', time_of_day: 'morning', instructions: '',
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try { setData(await api.getMedications()); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const logMedication = async (id: number, status: string) => {
    try {
      await api.logMedication(id, { status });
      loadData();
    } catch (e: any) { alert(e.message); }
  };

  const addMedication = async () => {
    if (!form.medicine_name.trim()) { setError('Medicine name is required.'); return; }
    setSaving(true);
    setError(null);
    try {
      await api.addMedication(form);
      setForm({ medicine_name: '', dosage: '', frequency: '', time_of_day: 'morning', instructions: '' });
      setShowAdd(false);
      loadData();
    } catch (e: any) { setError(e.message || 'Could not add medication.'); }
    finally { setSaving(false); }
  };

  const removeMedication = async (med: Medication) => {
    const label = med.medicine_name;
    const isDoctorMed = (med.source || 'doctor') === 'doctor';
    const message = isDoctorMed
      ? `Remove "${label}" from your tracked medications?\n\nThis medicine came from a doctor's prescription. Removing it only hides it from your reminders — the prescription record stays intact.`
      : `Remove "${label}" from your tracked medications?`;
    if (!window.confirm(message)) return;
    try {
      await api.removeMedication(med.id);
      loadData();
    } catch (e: any) { alert(e.message); }
  };

  if (loading) return <LoadingSpinner message="Loading medications..." />;

  const medications: Medication[] = data?.medications || [];

  if (!medications.length && !showAdd) {
    return (
      <div className="space-y-6">
        <Header onAdd={() => setShowAdd(true)} />
        <EmptyState
          title="No medications"
          description="Track a medicine you take regularly, or they'll appear here automatically when your doctor prescribes one."
        />
        {showAdd && <AddForm />}
      </div>
    );
  }

  const hasLogs = (data.total_doses || 0) > 0;
  const adherence = data.adherence_percentage || 0;
  const doctorMeds = medications.filter((m) => (m.source || 'doctor') === 'doctor');
  const patientMeds = medications.filter((m) => m.source === 'patient');

  return (
    <div className="space-y-6">
      <Header onAdd={() => setShowAdd((s) => !s)} addOpen={showAdd} />

      {showAdd && <AddForm />}

      {/* Adherence Card */}
      <div className="card bg-gradient-to-r from-purple-50 to-primary-50">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-sm">
            <span className="text-2xl font-bold text-primary-600">{hasLogs ? `${adherence}%` : '—'}</span>
          </div>
          <div>
            <h3 className="font-bold text-gray-900">Medication Adherence</h3>
            <p className="text-sm text-gray-600">
              {hasLogs
                ? `${data.doses_taken} of ${data.total_doses} doses taken`
                : 'No doses logged yet — tap ✓ below when you take a dose'}
            </p>
            <div className="w-48 h-2 bg-gray-200 rounded-full mt-2">
              <div className="h-full bg-primary-500 rounded-full" style={{ width: `${hasLogs ? adherence : 0}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Doctor-prescribed */}
      {doctorMeds.length > 0 && (
        <Section
          title="Prescribed by your doctor"
          icon={<Stethoscope size={15} className="text-blue-600" />}
          note="Added automatically from doctor prescriptions"
          meds={doctorMeds}
        />
      )}

      {/* Self-added */}
      {patientMeds.length > 0 && (
        <Section
          title="Added by me"
          icon={<User size={15} className="text-purple-600" />}
          note="Medicines you track yourself"
          meds={patientMeds}
        />
      )}

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-500 flex items-start gap-2">
        <Info size={14} className="mt-0.5 shrink-0" />
        <span>
          Doctor prescriptions add their medicines here automatically. You can add your own medicines (e.g. vitamins or OTC) with “Add medication”, and remove any entry — removing a doctor's medicine doesn't change the prescription.
        </span>
      </div>
    </div>
  );

  function Header({ onAdd, addOpen = false }: { onAdd: () => void; addOpen?: boolean }) {
    return (
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Pill className="text-purple-500" size={22} /> My Medications
        </h2>
        <button onClick={onAdd} className="btn-primary text-sm flex items-center gap-2">
          {addOpen ? <X size={15} /> : <Plus size={15} />} {addOpen ? 'Close' : 'Add medication'}
        </button>
      </div>
    );
  }

  function AddForm() {
    return (
      <div className="card border-purple-200">
        <h3 className="font-semibold text-gray-900 mb-3 text-sm flex items-center gap-2">
          <Plus size={15} className="text-purple-600" /> Track a medicine
        </h3>
        {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-gray-600">Medicine name *</label>
            <input
              className="input-field mt-1"
              value={form.medicine_name}
              onChange={(e) => setForm((f) => ({ ...f, medicine_name: e.target.value }))}
              placeholder="e.g. Vitamin D3, Paracetamol"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">Dosage</label>
            <input
              className="input-field mt-1"
              value={form.dosage}
              onChange={(e) => setForm((f) => ({ ...f, dosage: e.target.value }))}
              placeholder="e.g. 500 mg"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">Frequency</label>
            <input
              className="input-field mt-1"
              value={form.frequency}
              onChange={(e) => setForm((f) => ({ ...f, frequency: e.target.value }))}
              placeholder="e.g. twice daily"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">Time of day</label>
            <select
              className="input-field mt-1"
              value={form.time_of_day}
              onChange={(e) => setForm((f) => ({ ...f, time_of_day: e.target.value }))}
            >
              <option value="morning">Morning</option>
              <option value="afternoon">Afternoon</option>
              <option value="night">Night</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-medium text-gray-600">Notes (optional)</label>
            <input
              className="input-field mt-1"
              value={form.instructions}
              onChange={(e) => setForm((f) => ({ ...f, instructions: e.target.value }))}
              placeholder="e.g. after food"
            />
          </div>
        </div>
        <button onClick={addMedication} className="btn-primary mt-4 text-sm" disabled={saving}>
          {saving ? 'Adding…' : 'Add medication'}
        </button>
      </div>
    );
  }

  function MedRow({ med }: { med: Medication }) {
    const isDoctorMed = (med.source || 'doctor') === 'doctor';
    return (
      <div className="card">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-semibold text-gray-900">{med.medicine_name}</h4>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium inline-flex items-center gap-1 ${
                isDoctorMed ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
              }`}>
                {isDoctorMed ? <Stethoscope size={9} /> : <User size={9} />}
                {isDoctorMed ? 'Doctor' : 'Self-added'}
              </span>
            </div>
            <p className="text-sm text-gray-600">
              {med.dosage || '—'} • {med.frequency || 'as needed'}
              {med.time_of_day && <span className="text-xs text-gray-400 capitalize"> · {med.time_of_day}</span>}
            </p>
            {med.instructions && <p className="text-xs text-gray-500 mt-0.5">{med.instructions}</p>}
          </div>
          <div className="flex gap-2 shrink-0">
            <button onClick={() => logMedication(med.id, 'taken')} className="p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors" title="Taken">
              <Check size={16} />
            </button>
            <button onClick={() => logMedication(med.id, 'skipped')} className="p-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors" title="Skipped">
              <Minus size={16} />
            </button>
            <button onClick={() => logMedication(med.id, 'missed')} className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors" title="Missed">
              <X size={16} />
            </button>
            <button onClick={() => removeMedication(med)} className="p-2 bg-gray-100 text-gray-500 rounded-lg hover:bg-red-100 hover:text-red-600 transition-colors" title="Remove">
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  function Section({ title, icon, note, meds }: { title: string; icon: React.ReactNode; note: string; meds: Medication[] }) {
    return (
      <div>
        <div className="flex items-center gap-2 mb-2">
          {icon}
          <h3 className="font-semibold text-gray-800 text-sm">{title}</h3>
          <span className="text-xs text-gray-400">· {note}</span>
        </div>
        <div className="space-y-3">
          {meds.map((med) => <MedRow key={med.id} med={med} />)}
        </div>
      </div>
    );
  }
}
