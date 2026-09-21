import React, { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AlertBadge } from '../components/common/AlertBadge';
import {
  ArrowLeft, AlertTriangle, Info, MapPin, Phone,
  Shield, ArrowRight, Activity, CheckCircle2, AlertCircle
} from 'lucide-react';

export function ScreeningResultPage() {
  const { id } = useParams();
  const location = useLocation();
  const [fetched, setFetched] = useState<any>(null);
  const [fetchState, setFetchState] = useState<'loading' | 'ready' | 'failed'>('ready');
  const passedScreening = (location.state as any)?.screening;

  // Direct visits (refresh / bookmark / shared link) have no navigation state —
  // recover the stored assessment from the API instead of dead-ending.
  useEffect(() => {
    if (passedScreening || !id) return;
    setFetchState('loading');
    api.getCheckin(parseInt(id))
      .then(d => {
        const a = d.assessment;
        setFetched(a ? {
          urgency_level: a.urgency_level,
          possible_concerns: a.possible_concerns,
          reasons: a.reasons,
          recommended_action: a.recommended_action,
          warning_signs: a.warning_signs,
          care_route: a.care_route,
          red_flags_detected: a.urgency_level === 'emergency',
        } : null);
        setFetchState('ready');
      })
      .catch(() => setFetchState('failed'));
  }, [id, passedScreening]);

  const screening = passedScreening || fetched;

  if (!passedScreening && fetchState === 'loading') {
    return <LoadingSpinner message="Loading your screening result..." />;
  }

  if (!screening) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          {fetchState === 'failed' ? 'Unable to load screening' : 'No Screening Data'}
        </h2>
        <p className="text-gray-500 mb-4">Please complete a health check-in first.</p>
        <Link to="/patient/checkin" className="btn-primary">Start Health Check</Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/patient" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} /> Back to Dashboard
      </Link>

      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-900">AI-Assisted Preliminary Screening</h2>
        <p className="text-sm text-gray-500 mt-1">Based on your health check-in</p>
      </div>

      {/* Emergency Alert */}
      {screening.red_flags_detected && (
        <div className="bg-red-50 border-2 border-red-300 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <AlertTriangle className="text-red-600" size={28} />
            <div>
              <h3 className="text-lg font-bold text-red-800">POTENTIAL EMERGENCY DETECTED</h3>
              <p className="text-sm text-red-600">Potentially serious symptoms detected. Emergency medical evaluation is recommended.</p>
            </div>
          </div>
          {screening.emergency_guidance && (
            <div className="bg-white rounded-lg p-3 text-sm text-red-700 whitespace-pre-line mt-3">
              {screening.emergency_guidance}
            </div>
          )}
          {screening.red_flags && screening.red_flags.length > 0 && (
            <div className="mt-3 space-y-1">
              {screening.red_flags.map((rf: any, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm text-red-700">
                  <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
                  <span>{rf.description}</span>
                </div>
              ))}
            </div>
          )}
          <div className="mt-4 flex gap-3">
            <Link to="/patient/emergency" className="btn-emergency flex-1 text-center text-sm py-2">
              🆘 Emergency Help
            </Link>
          </div>
          <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-2 text-xs text-yellow-700 text-center">
            ⚠️ Demo Workflow — No real emergency services are contacted.
          </div>
        </div>
      )}

      {/* Urgency Level */}
      <div className="card">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">Urgency Assessment</h3>
          <AlertBadge level={screening.urgency_level} />
        </div>
        {screening.ai_service_used && (
          <p className="text-xs text-gray-400 mt-1">Service: {screening.ai_service_used === 'rule_based' ? 'Rule-based screening' : screening.ai_service_used === 'gemini' ? 'AI-assisted screening' : screening.ai_service_used}</p>
        )}
      </div>

      {/* Possible Concerns */}
      {screening.possible_concerns && screening.possible_concerns.length > 0 && (
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-3">Possible Health Concerns</h3>
          <div className="space-y-3">
            {screening.possible_concerns.map((c: any, i: number) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg">
                <p className="font-medium text-gray-800">{c.concern}</p>
                <p className="text-sm text-gray-600 mt-1">{c.reason}</p>
                {c.relevance && (
                  <span className={`text-xs font-medium mt-2 inline-block px-2 py-0.5 rounded-full ${
                    c.relevance === 'high' ? 'bg-orange-100 text-orange-700' :
                    c.relevance === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>{c.relevance} relevance</span>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3 italic">These are preliminary observations, not a diagnosis. A healthcare professional should evaluate you.</p>
        </div>
      )}

      {/* Reasons */}
      {screening.reasons && screening.reasons.length > 0 && (
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-3">Assessment Reasons</h3>
          <ul className="space-y-2">
            {screening.reasons.map((r: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <Info size={14} className="text-healthcare-500 mt-0.5 flex-shrink-0" />
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Action */}
      <div className="card border-primary-200 bg-primary-50/50">
        <h3 className="font-bold text-gray-900 mb-2">Recommended Action</h3>
        <p className="text-gray-700">{screening.recommended_action}</p>
      </div>

      {/* Warning Signs */}
      {screening.warning_signs && screening.warning_signs.length > 0 && (
        <div className="card border-yellow-200 bg-yellow-50">
          <h3 className="font-bold text-yellow-800 mb-2 flex items-center gap-2">
            <AlertTriangle size={18} /> Warning Signs
          </h3>
          <ul className="space-y-1">
            {screening.warning_signs.map((w: string, i: number) => (
              <li key={i} className="text-sm text-yellow-700">• {w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Care Route Summary */}
      {screening.care_route && (
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
            <MapPin size={18} className="text-healthcare-600" /> Care Route Recommendation
          </h3>
          <div className="space-y-2 text-sm">
            <p><span className="font-medium">Recommended Care Level:</span> {screening.care_route.recommended_care_level}</p>
            <p className="text-gray-600">{screening.care_route.how_serious}</p>
            <p className="text-gray-600">{screening.care_route.what_next}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link to="/patient/care-route" className="card text-center hover:shadow-md transition-shadow">
          <MapPin className="mx-auto mb-2 text-healthcare-500" size={24} />
          <span className="text-sm font-medium">Find Care Facilities</span>
        </Link>
        <Link to="/patient/health-memory" className="card text-center hover:shadow-md transition-shadow">
          <Activity className="mx-auto mb-2 text-primary-500" size={24} />
          <span className="text-sm font-medium">Health Memory</span>
        </Link>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-500">
        <Shield size={14} className="inline mr-1" />
        <strong>Medical Safety Notice:</strong> CareRoute AI provides preliminary screening only. This does NOT constitute medical diagnosis, treatment, or advice. Always consult a qualified healthcare provider.
      </div>
    </div>
  );
}
