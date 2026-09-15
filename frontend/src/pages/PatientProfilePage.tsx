import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { User, Save } from 'lucide-react';

export function PatientProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadProfile(); }, []);

  const loadProfile = async () => {
    try {
      const p = await api.getProfile();
      setProfile(p);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateProfile(profile);
      alert('Profile updated successfully');
    } catch (e: any) { alert('Error: ' + e.message); }
    finally { setSaving(false); }
  };

  const update = (field: string, value: any) => setProfile((p: any) => ({ ...p, [field]: value }));

  if (loading) return <LoadingSpinner />;
  if (!profile) return <p className="text-center py-12 text-gray-500">Profile not found</p>;

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <User className="text-primary-500" size={22} /> My Profile
      </h2>
      <form onSubmit={handleSave} className="card space-y-4">
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input className="input-field" value={profile.user_name || ''} disabled />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input className="input-field" value={profile.user_email || ''} disabled />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
            <input type="date" className="input-field" value={profile.date_of_birth || ''} onChange={e => update('date_of_birth', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
            <select className="input-field" value={profile.gender || ''} onChange={e => update('gender', e.target.value)}>
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Blood Group</label>
            <select className="input-field" value={profile.blood_group || ''} onChange={e => update('blood_group', e.target.value)}>
              <option value="">Select</option>
              {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Language</label>
            <select className="input-field" value={profile.preferred_language || 'en'} onChange={e => update('preferred_language', e.target.value)}>
              <option value="en">English</option>
              <option value="ta">Tamil</option>
              <option value="hi">Hindi</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <textarea className="input-field" rows={2} value={profile.address || ''} onChange={e => update('address', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Village</label>
            <input className="input-field" value={profile.village || ''} onChange={e => update('village', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
            <input className="input-field" value={profile.district || ''} onChange={e => update('district', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
            <input className="input-field" value={profile.state || ''} onChange={e => update('state', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Allergies</label>
            <input className="input-field" value={profile.allergies || ''} onChange={e => update('allergies', e.target.value)} placeholder="e.g., Peanuts, Penicillin" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Chronic Conditions</label>
            <input className="input-field" value={profile.chronic_conditions || ''} onChange={e => update('chronic_conditions', e.target.value)} placeholder="e.g., Diabetes, Hypertension" />
          </div>
        </div>
        <button type="submit" className="btn-primary flex items-center gap-2" disabled={saving}>
          <Save size={16} /> {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </form>
    </div>
  );
}
