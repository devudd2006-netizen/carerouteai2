import React, { useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AlertTriangle, Phone, MapPin, Heart, Shield, Share2, Download, Siren } from 'lucide-react';

export function EmergencyPage() {
  const [healthCard, setHealthCard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [cardGenerated, setCardGenerated] = useState(false);

  const generateCard = async () => {
    setLoading(true);
    try {
      const card = await api.generateHealthCard();
      setHealthCard(card);
      setCardGenerated(true);
    } catch (e: any) {
      alert('Error generating card: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-red-600 text-white rounded-xl p-6 text-center">
        <Siren className="mx-auto mb-3" size={40} />
        <h2 className="text-2xl font-bold">Emergency Help</h2>
        <p className="text-red-100 mt-1">If you are experiencing a medical emergency, call emergency services immediately.</p>
      </div>

      {/* Emergency Contacts */}
      <div className="card border-red-200">
        <h3 className="font-bold text-gray-900 mb-3">Emergency Numbers</h3>
        <div className="space-y-3">
          <a href="tel:108" className="flex items-center gap-3 p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
            <Phone className="text-red-600" size={20} />
            <div>
              <p className="font-semibold text-red-800">108 — Ambulance / Emergency</p>
              <p className="text-xs text-red-600">National Emergency Helpline</p>
            </div>
          </a>
          <a href="tel:112" className="flex items-center gap-3 p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
            <Phone className="text-red-600" size={20} />
            <div>
              <p className="font-semibold text-red-800">112 — Emergency Services</p>
              <p className="text-xs text-red-600">Single Emergency Number</p>
            </div>
          </a>
        </div>
      </div>

      {/* Emergency Health Card */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <Heart className="text-red-500" size={18} /> Emergency Health Card
          </h3>
          {!cardGenerated && (
            <button onClick={generateCard} disabled={loading} className="btn-primary text-sm">
              {loading ? 'Generating...' : 'Generate Card'}
            </button>
          )}
        </div>

        {loading && <LoadingSpinner message="Generating your emergency health card..." />}

        {healthCard && (
          <div className="bg-white border-2 border-red-200 rounded-xl p-6">
            <div className="text-center mb-4">
              <h4 className="font-bold text-lg text-gray-900">Emergency Health Card</h4>
              <p className="text-xs text-gray-500">Minimum necessary information for emergency care</p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Name</p>
                <p className="font-medium">{healthCard.patient_name}</p>
              </div>
              {healthCard.age && <div>
                <p className="text-gray-500">Age</p>
                <p className="font-medium">{healthCard.age} years</p>
              </div>}
              {healthCard.blood_group && <div>
                <p className="text-gray-500">Blood Group</p>
                <p className="font-medium">{healthCard.blood_group}</p>
              </div>}
              {healthCard.current_location && <div>
                <p className="text-gray-500">Location</p>
                <p className="font-medium">{healthCard.current_location}</p>
              </div>}
            </div>
            {healthCard.allergies && healthCard.allergies.length > 0 && (
              <div className="mt-3">
                <p className="text-gray-500 text-sm">Allergies</p>
                <p className="font-medium text-sm">{healthCard.allergies.join(', ')}</p>
              </div>
            )}
            {healthCard.medical_conditions && healthCard.medical_conditions.length > 0 && (
              <div className="mt-2">
                <p className="text-gray-500 text-sm">Medical Conditions</p>
                <p className="font-medium text-sm">{healthCard.medical_conditions.join(', ')}</p>
              </div>
            )}
            {healthCard.emergency_contact_name && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-500 text-xs">Emergency Contact</p>
                <p className="font-medium text-sm">{healthCard.emergency_contact_name} — {healthCard.emergency_contact_phone}</p>
              </div>
            )}
            {healthCard.share_token && (
              <div className="mt-3 p-2 bg-blue-50 rounded-lg text-xs text-blue-700">
                <Share2 size={12} className="inline mr-1" />
                Share token generated. Card expires in 24 hours.
              </div>
            )}
            <p className="mt-3 text-xs text-gray-400 italic">This card contains minimum necessary information only.</p>
          </div>
        )}

        {!cardGenerated && !loading && (
          <div className="text-center py-6 text-gray-500 text-sm">
            <p>Generate an Emergency Health Card with essential information that can be shared with emergency responders.</p>
          </div>
        )}
      </div>

      {/* Demo Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-700">
        <strong>Demo Emergency Workflow</strong> — No real emergency services are contacted. In a production system, this would be integrated with configured emergency response services with explicit user consent.
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-500">
        <Shield size={14} className="inline mr-1" />
        Emergency detection is based on deterministic medical safety rules. AI may provide additional context, but red-flag rules always take priority.
      </div>
    </div>
  );
}
