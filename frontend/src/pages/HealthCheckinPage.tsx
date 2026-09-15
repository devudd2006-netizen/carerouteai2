import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  Activity, Thermometer, Wind, Heart, Brain, Zap,
  Droplets, Moon, Coffee, Pill, MessageSquare, ArrowRight, ArrowLeft, Send
} from 'lucide-react';

interface SymptomState {
  feeling_today: string;
  fever: boolean;
  fever_temperature: string;
  cough: boolean;
  breathing_difficulty: boolean;
  chest_discomfort: boolean;
  headache: boolean;
  dizziness: boolean;
  weakness: boolean;
  pain: boolean;
  pain_location: string;
  pain_severity: number;
  vomiting: boolean;
  diarrhea: boolean;
  sleep_quality: number;
  stress_level: number;
  medication_taken: boolean;
  new_symptoms_text: string;
}

const STEPS = [
  { id: 'greeting', title: 'How are you feeling?' },
  { id: 'symptoms', title: 'Symptom Check' },
  { id: 'details', title: 'Additional Details' },
  { id: 'review', title: 'Review & Submit' },
];

export function HealthCheckinPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<SymptomState>({
    feeling_today: '', fever: false, fever_temperature: '', cough: false,
    breathing_difficulty: false, chest_discomfort: false, headache: false,
    dizziness: false, weakness: false, pain: false, pain_location: '',
    pain_severity: 5, vomiting: false, diarrhea: false, sleep_quality: 3,
    stress_level: 3, medication_taken: true, new_symptoms_text: '',
  });

  const update = (field: keyof SymptomState, value: any) =>
    setData(d => ({ ...d, [field]: value }));

  const symptoms = [
    { key: 'fever', label: 'Fever', icon: Thermometer, temp: true },
    { key: 'cough', label: 'Cough', icon: Wind },
    { key: 'breathing_difficulty', label: 'Breathing Difficulty', icon: Wind },
    { key: 'chest_discomfort', label: 'Chest Discomfort', icon: Heart },
    { key: 'headache', label: 'Headache', icon: Brain },
    { key: 'dizziness', label: 'Dizziness', icon: Zap },
    { key: 'weakness', label: 'Weakness', icon: Activity },
    { key: 'pain', label: 'Pain', icon: Droplets, details: true },
    { key: 'vomiting', label: 'Vomiting', icon: Droplets },
    { key: 'diarrhea', label: 'Diarrhea', icon: Droplets },
  ];

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      // Sanitize numeric fields: empty strings and inactive pain severity
      // must be sent as null, not '' / stale numbers (Pydantic float validation).
      const payload = {
        ...data,
        fever_temperature:
          data.fever && data.fever_temperature !== ''
            ? Number(data.fever_temperature)
            : null,
        pain_location: data.pain ? data.pain_location : null,
        pain_severity: data.pain ? data.pain_severity : null,
        new_symptoms_text: data.new_symptoms_text || null,
      };
      const result = await api.createCheckin(payload);
      navigate(`/patient/screening/${result.checkin_id}`, { state: { screening: result.screening, checkin_id: result.checkin_id } });
    } catch (err: any) {
      setError(err.message || 'Unable to submit check-in. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const activeSymptoms = symptoms.filter(s => data[s.key as keyof SymptomState]);

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 mb-2">Health Check-in</h2>
      <p className="text-gray-500 text-sm mb-6">Let's check how you're doing today.</p>

      {/* Progress */}
      <div className="flex gap-2 mb-8">
        {STEPS.map((s, i) => (
          <div key={s.id} className="flex-1">
            <div className={`h-1.5 rounded-full ${i <= step ? 'bg-primary-500' : 'bg-gray-200'}`} />
            <p className={`text-xs mt-1 ${i <= step ? 'text-primary-600 font-medium' : 'text-gray-400'}`}>{s.title}</p>
          </div>
        ))}
      </div>

      {submitting ? (
        <div className="card text-center py-12">
          <LoadingSpinner message="Analyzing your health check-in..." />
          <p className="text-sm text-gray-500 mt-4">Running AI-assisted preliminary screening...</p>
        </div>
      ) : (
        <div className="card">
          {/* Step 0: Feeling */}
          {step === 0 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">How are you feeling today? 👋</h3>
              <div className="grid grid-cols-2 gap-3">
                {['good', 'okay', 'bad', 'terrible'].map(feeling => (
                  <button
                    key={feeling}
                    onClick={() => update('feeling_today', feeling)}
                    className={`p-4 rounded-xl border-2 text-center font-medium capitalize transition-all ${
                      data.feeling_today === feeling
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {feeling === 'good' ? '😊' : feeling === 'okay' ? '🙂' : feeling === 'bad' ? '😟' : '😰'} {feeling}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="meds" checked={data.medication_taken} onChange={e => update('medication_taken', e.target.checked)} className="w-4 h-4 text-primary-600 rounded" />
                <label htmlFor="meds" className="text-sm text-gray-700">I've taken my medications today</label>
              </div>
              <button onClick={() => setStep(1)} className="btn-primary w-full flex items-center justify-center gap-2" disabled={!data.feeling_today}>
                Continue <ArrowRight size={16} />
              </button>
            </div>
          )}

          {/* Step 1: Symptoms */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Any of these symptoms?</h3>
              <p className="text-sm text-gray-500">Select all that apply.</p>
              <div className="grid grid-cols-2 gap-3">
                {symptoms.map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => update(key as keyof SymptomState, !data[key as keyof SymptomState])}
                    className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all text-left ${
                      data[key as keyof SymptomState]
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Icon size={20} className={data[key as keyof SymptomState] ? 'text-primary-600' : 'text-gray-400'} />
                    <span className="text-sm font-medium">{label}</span>
                  </button>
                ))}
              </div>
              {data.fever && (
                <div className="mt-4">
                  <label className="text-sm font-medium text-gray-700">Temperature (°F)</label>
                  <input type="number" className="input-field mt-1" value={data.fever_temperature} onChange={e => update('fever_temperature', e.target.value)} placeholder="e.g., 101.5" />
                </div>
              )}
              {data.pain && (
                <div className="mt-4">
                  <label className="text-sm font-medium text-gray-700">Pain Location</label>
                  <input type="text" className="input-field mt-1" value={data.pain_location} onChange={e => update('pain_location', e.target.value)} placeholder="e.g., Head, Stomach, Back..." />
                  <label className="text-sm font-medium text-gray-700 mt-3 block">Pain Severity (1-10)</label>
                  <input type="range" min="1" max="10" value={data.pain_severity} onChange={e => update('pain_severity', parseInt(e.target.value))} className="w-full mt-1" />
                  <span className="text-sm text-gray-600">{data.pain_severity}/10</span>
                </div>
              )}
              <div className="flex gap-3 mt-6">
                <button onClick={() => setStep(0)} className="btn-secondary flex-1 flex items-center justify-center gap-2"><ArrowLeft size={16} /> Back</button>
                <button onClick={() => setStep(2)} className="btn-primary flex-1 flex items-center justify-center gap-2">Continue <ArrowRight size={16} /></button>
              </div>
            </div>
          )}

          {/* Step 2: Details */}
          {step === 2 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">A few more details</h3>
              <div>
                <label className="text-sm font-medium text-gray-700">Sleep quality (1=Poor, 5=Great)</label>
                <input type="range" min="1" max="5" value={data.sleep_quality} onChange={e => update('sleep_quality', parseInt(e.target.value))} className="w-full mt-2" />
                <div className="flex justify-between text-xs text-gray-400"><span>Poor</span><span>{data.sleep_quality}/5</span><span>Great</span></div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Stress level (1=Low, 5=High)</label>
                <input type="range" min="1" max="5" value={data.stress_level} onChange={e => update('stress_level', parseInt(e.target.value))} className="w-full mt-2" />
                <div className="flex justify-between text-xs text-gray-400"><span>Low</span><span>{data.stress_level}/5</span><span>High</span></div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Any other symptoms or notes?</label>
                <textarea className="input-field mt-1" rows={3} value={data.new_symptoms_text} onChange={e => update('new_symptoms_text', e.target.value)} placeholder="Describe any other symptoms or concerns..." />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setStep(1)} className="btn-secondary flex-1 flex items-center justify-center gap-2"><ArrowLeft size={16} /> Back</button>
                <button onClick={() => setStep(3)} className="btn-primary flex-1 flex items-center justify-center gap-2">Review <ArrowRight size={16} /></button>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Review Your Check-in</h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                <p><span className="font-medium">Feeling:</span> {data.feeling_today}</p>
                <p><span className="font-medium">Medications taken:</span> {data.medication_taken ? 'Yes' : 'No'}</p>
                <p><span className="font-medium">Sleep:</span> {data.sleep_quality}/5 | <span className="font-medium">Stress:</span> {data.stress_level}/5</p>
                {activeSymptoms.length > 0 && (
                  <div>
                    <span className="font-medium">Symptoms:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {activeSymptoms.map(s => <span key={s.key} className="bg-primary-100 text-primary-700 text-xs px-2 py-1 rounded-full">{s.label}</span>)}
                    </div>
                  </div>
                )}
                {data.new_symptoms_text && <p><span className="font-medium">Notes:</span> {data.new_symptoms_text}</p>}
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
                ⚠️ This screening provides preliminary analysis only. It does NOT constitute medical diagnosis or advice.
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700" role="alert">
                  {error}
                </div>
              )}
              <div className="flex gap-3">
                <button onClick={() => setStep(2)} className="btn-secondary flex-1 flex items-center justify-center gap-2"><ArrowLeft size={16} /> Edit</button>
                <button onClick={handleSubmit} disabled={submitting} className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-60"><Send size={16} /> {submitting ? 'Analyzing your health check...' : 'Submit Check-in'}</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
