import React, { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { MapPin, AlertTriangle, Info, Tent } from 'lucide-react';
// Leaflet is bundled with the app (npm) — no global script tag needed.
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export function CommunityMapPage() {
  const [communities, setCommunities] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);
  const [generatingCamp, setGeneratingCamp] = useState(false);
  const [campResult, setCampResult] = useState<any>(null);
  // Leaflet owns this container's children — React must never render into it.
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    loadData();
    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  const loadData = async () => {
    try {
      const data = await api.getCommunityPriorityMap();
      setCommunities(data.communities || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (!loading && communities.length > 0 && !mapReady) initMap();
  }, [loading, communities]);

  const initMap = () => {
    if (typeof window === 'undefined' || !mapRef.current || leafletMapRef.current) return;
    try {
      const map = L.map(mapRef.current).setView([9.95, 78.0], 10);
      leafletMapRef.current = map;
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
      }).addTo(map);

      const colors: Record<string, string> = { low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#dc2626' };

      communities.forEach(c => {
        const color = colors[c.priority_level] || '#666';
        const radius = 8 + (c.priority_score / 10);
        const circle = L.circleMarker([c.latitude, c.longitude], {
          radius, fillColor: color, color: '#fff', weight: 2, fillOpacity: 0.8,
        }).addTo(map);

        circle.bindPopup(`
          <strong>${c.community_name}</strong><br/>
          Priority: ${c.priority_level} (${c.priority_score})<br/>
          Population: ${c.population?.toLocaleString()}<br/>
          <button onclick="window.__selectCommunity(${c.community_id})" style="margin-top:4px;padding:2px 8px;background:#0ea5e9;color:white;border:none;border-radius:4px;cursor:pointer">View Details</button>
        `);

        circle.on('click', () => {
          setSelected(c);
        });
      });

      (window as any).__selectCommunity = (id: number) => {
        const c = communities.find(cm => cm.community_id === id);
        if (c) setSelected(c);
      };

      setMapReady(true);
    } catch (e) { console.error('Map init failed:', e); }
  };

  const generateCamp = async () => {
    if (!selected) return;
    setGeneratingCamp(true);
    try {
      const data = await api.getCampRecommendations({ community_id: selected.community_id });
      setCampResult(data.recommendations?.[0] || null);
    } catch (e: any) { alert(e.message); }
    finally { setGeneratingCamp(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <MapPin className="text-healthcare-600" size={22} /> Healthcare Gap Map
        </h2>
        <p className="text-sm text-gray-500">Community Care Priority Index visualization</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2">
          <div className="card p-0 overflow-hidden relative">
            <div ref={mapRef} className="h-[500px] bg-gray-100 z-0" />
            {!mapReady && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                {loading ? <LoadingSpinner /> : <p className="text-gray-400">Preparing map…</p>}
              </div>
            )}
          </div>
          <div className="flex gap-4 mt-3 text-xs">
            {[{ color: '#22c55e', label: 'Low Priority' }, { color: '#eab308', label: 'Medium' }, { color: '#f97316', label: 'High' }, { color: '#dc2626', label: 'Critical' }].map(({ color, label }) => (
              <span key={label} className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full" style={{ background: color }} /> {label}
              </span>
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selected ? (
            <>
              <div className="card">
                <h3 className="font-bold text-gray-900 mb-3">{selected.community_name}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">Priority Level</span>
                    <span className={`font-semibold px-2 py-0.5 rounded-full text-xs ${
                      selected.priority_level === 'critical' ? 'bg-red-100 text-red-700' :
                      selected.priority_level === 'high' ? 'bg-orange-100 text-orange-700' :
                      selected.priority_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>{selected.priority_level?.toUpperCase()}</span>
                  </div>
                  <div className="flex justify-between"><span className="text-gray-500">Score</span><span className="font-bold">{selected.priority_score}/100</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Population</span><span>{selected.population?.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">District</span><span>{selected.district}</span></div>
                </div>
              </div>

              {selected.reasons && selected.reasons.length > 0 && (
                <div className="card">
                  <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-1"><Info size={14} /> Reasons</h4>
                  <ul className="space-y-1">
                    {selected.reasons.map((r: string, i: number) => (
                      <li key={i} className="text-sm text-gray-600 flex items-start gap-1">
                        <AlertTriangle size={12} className="text-orange-500 mt-0.5 flex-shrink-0" /> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <button onClick={generateCamp} disabled={generatingCamp} className="btn-primary w-full flex items-center justify-center gap-2">
                <Tent size={16} /> {generatingCamp ? 'Generating...' : 'Recommend Medical Camp'}
              </button>

              {campResult && (
                <div className="card border-primary-200 bg-primary-50">
                  <h4 className="font-bold text-gray-900 mb-2">🏕️ Camp Recommendation</h4>
                  <p className="text-sm text-gray-600">{campResult.reason}</p>
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-700">Suggested Services:</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {(campResult.suggested_services || []).map((s: string, i: number) => (
                        <span key={i} className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Duration: {campResult.suggested_duration_days} days • Population: ~{campResult.population_affected?.toLocaleString()}
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="card text-center py-8">
              <MapPin className="mx-auto text-gray-300 mb-2" size={32} />
              <p className="text-gray-500 text-sm">Select a community on the map to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
