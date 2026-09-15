import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Pill, Check, X, Minus, TrendingUp } from 'lucide-react';

export function MedicationsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) return <LoadingSpinner message="Loading medications..." />;
  if (!data || !data.medications?.length) {
    return <EmptyState title="No medications" description="No active medication reminders. Medications are added through doctor prescriptions." />;
  }

  const adherence = data.adherence_percentage || 100;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
        <Pill className="text-purple-500" size={22} /> My Medications
      </h2>

      {/* Adherence Card */}
      <div className="card bg-gradient-to-r from-purple-50 to-primary-50">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-sm">
            <span className="text-2xl font-bold text-primary-600">{adherence}%</span>
          </div>
          <div>
            <h3 className="font-bold text-gray-900">Medication Adherence</h3>
            <p className="text-sm text-gray-600">{data.doses_taken} of {data.total_doses} doses taken</p>
            <div className="w-48 h-2 bg-gray-200 rounded-full mt-2">
              <div className="h-full bg-primary-500 rounded-full" style={{ width: `${adherence}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Medication List */}
      <div className="space-y-3">
        {data.medications.map((med: any) => (
          <div key={med.id} className="card">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-gray-900">{med.medicine_name}</h4>
                <p className="text-sm text-gray-600">{med.dosage} • {med.frequency}</p>
                {med.time_of_day && <p className="text-xs text-gray-400 capitalize">{med.time_of_day}</p>}
              </div>
              <div className="flex gap-2">
                <button onClick={() => logMedication(med.id, 'taken')} className="p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors" title="Taken">
                  <Check size={16} />
                </button>
                <button onClick={() => logMedication(med.id, 'skipped')} className="p-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors" title="Skipped">
                  <Minus size={16} />
                </button>
                <button onClick={() => logMedication(med.id, 'missed')} className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors" title="Missed">
                  <X size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-500">
        💊 Medication reminders are generated from doctor-approved prescriptions only. Never modify prescriptions without consulting your doctor.
      </div>
    </div>
  );
}
