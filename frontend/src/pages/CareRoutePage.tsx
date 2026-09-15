import React, { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { MapPin, Phone, Clock, Star, Navigation, Search } from 'lucide-react';
// Leaflet is bundled with the app (npm) — no global script tag needed.
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export function CareRoutePage() {
  const [facilities, setFacilities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [mapReady, setMapReady] = useState(false);
  // Leaflet owns this container's children — React must never render into it.
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    loadFacilities();
    // Cleanup: destroy the map when the page unmounts so a remount starts fresh.
    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  const loadFacilities = async () => {
    try {
      const data = await api.getFacilities();
      setFacilities(data.facilities || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredFacilities = facilities.filter(f => {
    if (filter && f.facility_type !== filter) return false;
    if (searchQuery && !f.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  useEffect(() => {
    if (!loading && facilities.length > 0 && !mapReady) {
      initMap();
    }
  }, [loading, facilities]);

  const initMap = () => {
    if (typeof window === 'undefined' || !mapRef.current || leafletMapRef.current) return;
    try {
      const map = L.map(mapRef.current).setView([9.93, 78.12], 10);
      leafletMapRef.current = map;
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(map);

      const typeColors: Record<string, string> = {
        hospital: '#dc2626', phc: '#16a34a', chc: '#2563eb',
        clinic: '#9333ea', pharmacy: '#ea580c', diagnostic: '#0891b2', emergency: '#dc2626',
      };

      facilities.forEach(f => {
        const color = typeColors[f.facility_type] || '#666';
        const icon = L.divIcon({
          className: 'custom-marker',
          html: `<div style="background:${color};width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
          iconSize: [12, 12],
        });
        L.marker([f.latitude, f.longitude], { icon })
          .addTo(map)
          .bindPopup(`<strong>${f.name}</strong><br/>${f.facility_type}<br/>${f.address || ''}`);
      });
      setMapReady(true);
    } catch (e) {
      console.error('Map init failed:', e);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <MapPin className="text-healthcare-600" size={22} /> Find Appropriate Care
        </h2>
        <p className="text-sm text-gray-500">Healthcare facilities near you</p>
      </div>

      {/* Map — Leaflet container is ref-owned; overlays are siblings, never children */}
      <div className="card p-0 overflow-hidden relative">
        <div ref={mapRef} className="h-[400px] bg-gray-100 z-0" />
        {!mapReady && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            {loading ? <LoadingSpinner /> : <p className="text-gray-400">Preparing map…</p>}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
          <input type="text" className="input-field pl-9" placeholder="Search facilities..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
        <div className="flex gap-2 flex-wrap">
          {['', 'hospital', 'phc', 'chc', 'clinic', 'pharmacy', 'diagnostic', 'emergency'].map(type => (
            <button key={type} onClick={() => setFilter(type)} className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${filter === type ? 'bg-healthcare-600 text-white border-healthcare-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'}`}>
              {type || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Facility List */}
      {loading ? (
        <LoadingSpinner message="Loading facilities..." />
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {filteredFacilities.map(f => (
            <div key={f.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900">{f.name}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  f.facility_type === 'hospital' ? 'bg-red-100 text-red-700' :
                  f.facility_type === 'phc' ? 'bg-green-100 text-green-700' :
                  f.facility_type === 'chc' ? 'bg-blue-100 text-blue-700' :
                  f.facility_type === 'emergency' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{f.facility_type}</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{f.address}</p>
              <div className="flex flex-wrap gap-1 mb-2">
                {(f.services || []).slice(0, 4).map((s: string, i: number) => (
                  <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{s}</span>
                ))}
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                {f.distance_km && <span className="flex items-center gap-1"><Navigation size={12} /> {f.distance_km} km</span>}
                {f.contact_number && <span className="flex items-center gap-1"><Phone size={12} /> {f.contact_number}</span>}
                {f.opening_hours && <span className="flex items-center gap-1"><Clock size={12} /> {f.opening_hours}</span>}
              </div>
              {f.emergency_available && <span className="mt-2 inline-block text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded font-medium">🚨 Emergency Available</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
