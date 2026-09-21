import React, { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  MapPin, Phone, Clock, Navigation, Search, LocateFixed, Crosshair,
  Route as RouteIcon, ExternalLink, Siren, Award, X, Star,
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const MADURAI = { lat: 9.9252, lon: 78.1198 }; // default map center

type Facility = {
  id: number;
  name: string;
  facility_type: string;
  latitude: number;
  longitude: number;
  address: string | null;
  services: string[];
  emergency_available: boolean;
  opening_hours: string | null;
  contact_number: string | null;
  distance_km: number | null;
  capability_score?: number;
  rank_score?: number;
};

type RouteData = {
  coordinates: [number, number][];
  distance_km: number;
  duration_min: number;
  steps: { text: string; distance_m: number; name: string }[];
};

// ---------- helpers ----------

function formatDistance(km: number | null | undefined): string {
  if (km == null) return '';
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

function formatDuration(min: number): string {
  if (min < 60) return `${Math.round(min)} min`;
  const h = Math.floor(min / 60);
  return `${h} h ${Math.round(min % 60)} min`;
}

function straightLineKm(a: { lat: number; lon: number }, b: { latitude: number; longitude: number }): number {
  const R = 6371;
  const dLat = ((b.latitude - a.lat) * Math.PI) / 180;
  const dLon = ((b.longitude - a.lon) * Math.PI) / 180;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((a.lat * Math.PI) / 180) * Math.cos((b.latitude * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.asin(Math.sqrt(s));
}

/**
 * Turn OSRM step maneuvers into short human instructions, similar to how
 * navigation apps phrase them. Falls back to the road name.
 */
function maneuverToText(step: any): string {
  const m = step.maneuver || {};
  const type = m.type || '';
  const modifier = m.modifier || '';
  const road = step.name ? ` onto ${step.name}` : '';
  if (type === 'depart') return step.name ? `Head along ${step.name}` : 'Start';
  if (type === 'arrive') return 'Arrive at your destination';
  if (type === 'roundabout' || type === 'rotary') return `At the roundabout, take the exit${road}`;
  if (type === 'merge') return `Merge${road}`;
  if (type === 'fork') return `Keep ${modifier || 'straight'} at the fork${road}`;
  if (type === 'end of road') return `Turn ${modifier || 'right'}${road}`;
  if (type === 'turn') {
    if (modifier === 'straight') return `Continue straight${road}`;
    if (modifier === 'uturn') return `Make a U-turn${road}`;
    if (modifier === 'slight left' || modifier === 'slight right') return `Slight ${modifier.split(' ')[1]}${road}`;
    return `Turn ${modifier || 'right'}${road}`;
  }
  if (type === 'continue') return modifier === 'uturn' ? `Make a U-turn${road}` : `Continue${road}`;
  if (type === 'new name') return `Continue${road}`;
  return step.name ? `Continue along ${step.name}` : 'Continue';
}

export function CareRoutePage() {
  const [allFacilities, setAllFacilities] = useState<Facility[]>([]);
  const [nearbyBest, setNearbyBest] = useState<Facility[]>([]);
  const [overallBest, setOverallBest] = useState<Facility[]>([]);
  const [userPos, setUserPos] = useState<{ lat: number; lon: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [locationNote, setLocationNote] = useState<string | null>(null);
  const [locSource, setLocSource] = useState<'gps' | 'profile' | 'map' | null>(null);
  const [bestMeta, setBestMeta] = useState<{ used_fallback: boolean; radius_km: number } | null>(null);
  const [picking, setPicking] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('hospital');
  const [searchQuery, setSearchQuery] = useState('');
  const [selected, setSelected] = useState<Facility | null>(null);
  const [route, setRoute] = useState<RouteData | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Leaflet owns the container's children — React must never render into it.
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.LayerGroup | null>(null);
  const routeLayerRef = useRef<L.LayerGroup | null>(null);
  const youMarkerRef = useRef<L.CircleMarker | null>(null);

  // ---------------- data loading ----------------

  const loadFacilities = async (pos?: { lat: number; lon: number } | null) => {
    setLoading(true);
    try {
      const data = await api.getFacilities();
      const list: Facility[] = data.facilities || [];
      setAllFacilities(list);

      // Best-hospitals ranking needs the caller's coordinates when available.
      if (pos) {
        const best = await api.getBestHospitals(pos.lat, pos.lon);
        setNearbyBest(best.nearby_best || []);
        setOverallBest(best.overall_best || []);
        setBestMeta({ used_fallback: !!best.used_fallback, radius_km: best.radius_km || 15 });
      } else {
        const best = await api.getBestHospitals();
        setNearbyBest([]);
        setOverallBest(best.overall_best || []);
        setBestMeta(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Start with the profile's saved location (instant), then try the device
    // GPS for a precise fix. Whichever resolves updates the ranking.
    api.getProfile()
      .then((p) => {
        if (p?.latitude != null && p?.longitude != null) {
          const pos = { lat: p.latitude, lon: p.longitude };
          setUserPos(pos);
          return pos;
        }
        return null;
      })
      .then((pos) => {
        loadFacilities(pos);
        requestBrowserLocation(false);
      })
      .catch(() => {
        loadFacilities(null);
        requestBrowserLocation(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const requestBrowserLocation = (manual: boolean) => {
    if (!('geolocation' in navigator)) {
      if (manual) setLocationNote('Location is not supported on this device/browser. Use “Set on map” instead.');
      return;
    }
    setLocating(true);
    setLocationNote(null);
    const opts: PositionOptions = { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 };
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const pos = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        };
        setUserPos(pos);
        setLocSource('gps');
        setLocating(false);
        setLocationNote(`Using your precise GPS location (±${Math.round(position.coords.accuracy)} m).`);
        loadFacilities(pos);
        mapRef.current?.setView([pos.lat, pos.lon], 14);
      },
      (firstErr) => {
        // High-accuracy fixes often fail indoors or on desktops — retry once
        // with low accuracy before giving up.
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const pos = { lat: position.coords.latitude, lon: position.coords.longitude };
            setUserPos(pos);
            setLocSource('gps');
            setLocating(false);
            setLocationNote(`Using your approximate GPS location (±${Math.round(position.coords.accuracy)} m).`);
            loadFacilities(pos);
            mapRef.current?.setView([pos.lat, pos.lon], 12);
          },
          () => {
            setLocating(false);
            setLocationNote(
              firstErr.code === firstErr.PERMISSION_DENIED
                ? 'Location permission denied — using your saved home location. Tap “Set on map” to fine-tune it.'
                : 'Could not sense your location — using your saved home location. Tap “Set on map” to correct it.'
            );
          },
          { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }
        );
      },
      opts
    );
  };

  // ---------------- map ----------------

  useEffect(() => {
    if (loading || allFacilities.length === 0 || mapReady || !mapDivRef.current) return;
    try {
      const map = L.map(mapDivRef.current).setView(
        userPos ? [userPos.lat, userPos.lon] : [MADURAI.lat, MADURAI.lon],
        userPos ? 12 : 10
      );
      mapRef.current = map;
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);
      routeLayerRef.current = L.layerGroup().addTo(map);
      markersRef.current = L.layerGroup().addTo(map);
      setMapReady(true);
    } catch (e) {
      console.error('Map init failed:', e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, allFacilities]);

  // Draw hospital markers whenever the visible set changes
  useEffect(() => {
    const map = mapRef.current;
    const layer = markersRef.current;
    if (!map || !layer) return;
    layer.clearLayers();

    const typeColors: Record<string, string> = {
      hospital: '#dc2626', phc: '#16a34a', chc: '#2563eb',
      clinic: '#9333ea', pharmacy: '#ea580c', diagnostic: '#0891b2', emergency: '#dc2626',
    };

    visibleFacilities.forEach((f) => {
      const color = typeColors[f.facility_type] || '#666';
      const isBest = nearbyBest.some((b) => b.id === f.id) || overallBest.slice(0, 3).some((b) => b.id === f.id);
      const size = isBest ? 18 : 12;
      const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
        iconSize: [size, size],
      });
      const marker = L.marker([f.latitude, f.longitude], { icon })
        .addTo(layer)
        .bindPopup(
          `<strong>${f.name}</strong><br/>${formatDistance(f.distance_km)} · ${f.facility_type.toUpperCase()}<br/><small>${f.address || ''}</small>`
        );
      marker.on('click', () => selectFacility(f));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allFacilities, filter, searchQuery, nearbyBest, overallBest, mapReady]);

  // ---------------- routing ----------------

  const buildRoute = async (f: Facility, from: { lat: number; lon: number }) => {
    setRouteLoading(true);
    setRouteError(null);
    setRoute(null);
    try {
      const data = await fetch(
        `https://router.project-osrm.org/route/v1/driving/${from.lon},${from.lat};${f.longitude},${f.latitude}?overview=full&geometries=geojson&steps=true`
      ).then((r) => {
        if (!r.ok) throw new Error('Routing service unavailable');
        return r.json();
      });

      if (data.code !== 'Ok' || !data.routes?.length) {
        throw new Error('No road route found to this hospital');
      }
      const r = data.routes[0];
      setRoute({
        coordinates: r.geometry.coordinates.map((c: [number, number]) => [c[1], c[0]]),
        distance_km: r.distance / 1000,
        duration_min: r.duration / 60,
        steps: r.legs[0].steps.map((s: any) => ({
          text: maneuverToText(s),
          distance_m: s.distance,
          name: s.name || '',
        })),
      });
    } catch (e: any) {
      console.error(e);
      setRouteError(
        'Could not fetch the road route (routing service may be unreachable). Showing straight-line distance instead — use “Open in Google Maps” for turn-by-turn navigation.'
      );
      // Fallback: straight line so the map still shows something meaningful
      setRoute({
        coordinates: [[from.lat, from.lon], [f.latitude, f.longitude]],
        distance_km: straightLineKm(from, f),
        duration_min: 0,
        steps: [],
      });
    } finally {
      setRouteLoading(false);
    }
  };

  const selectFacility = (f: Facility) => {
    setSelected(f);
    setRoute(null);
    setRouteError(null);
    const from = userPos || ((): { lat: number; lon: number } => {
      // No location: fall back to map center so routing still works
      const c = mapRef.current?.getCenter();
      return c ? { lat: c.lat, lon: c.lng } : MADURAI;
    })();
    buildRoute(f, from);
  };

  const clearRoute = () => {
    setSelected(null);
    setRoute(null);
    setRouteError(null);
    if (routeLayerRef.current) routeLayerRef.current.clearLayers();
  };

  // Draw/clear the route polyline when it changes
  useEffect(() => {
    const map = mapRef.current;
    const layer = routeLayerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    if (selected && route) {
      const line = L.polyline(route.coordinates, { color: '#2563eb', weight: 5, opacity: 0.85 });
      line.addTo(layer);
      L.circleMarker([selected.latitude, selected.longitude], {
        radius: 8, color: '#dc2626', fillColor: '#dc2626', fillOpacity: 1, weight: 2,
      }).addTo(layer).bindTooltip(selected.name);
      if (userPos) {
        L.circleMarker([userPos.lat, userPos.lon], {
          radius: 7, color: '#2563eb', fillColor: '#60a5fa', fillOpacity: 1, weight: 2,
        }).addTo(layer).bindTooltip('You');
      }
      map.fitBounds(line.getBounds().pad(0.15));
    }
  }, [route, selected]);

  // Persistent "You are here" marker, redrawn whenever the location changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !userPos) return;
    youMarkerRef.current?.remove();
    youMarkerRef.current = L.circleMarker([userPos.lat, userPos.lon], {
      radius: 8, color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 1, weight: 3,
    }).addTo(map).bindTooltip('You are here');
  }, [userPos, mapReady]);

  // "Set on map" mode: next map click sets the user's location
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!picking) return;
    const container = map.getContainer();
    container.style.cursor = 'crosshair';
    const onClick = (e: L.LeafletMouseEvent) => {
      const pos = { lat: e.latlng.lat, lon: e.latlng.lng };
      setUserPos(pos);
      setLocSource('map');
      setPicking(false);
      setLocationNote('Location set from map — ranking updated.');
      loadFacilities(pos);
      api.updateProfile({ latitude: pos.lat, longitude: pos.lon }).catch(() => {});
    };
    map.on('click', onClick);
    return () => {
      container.style.cursor = '';
      map.off('click', onClick);
    };
  }, [picking, mapReady]);

  // ---------------- derived ----------------

  const visibleFacilities = allFacilities.filter((f) => {
    if (filter && f.facility_type !== filter) return false;
    if (searchQuery && !f.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const bestIds = new Set([...nearbyBest.slice(0, 3), ...overallBest.slice(0, 3)].map((f) => f.id));

  const FacilityCard = ({ f, highlight = false }: { f: Facility; highlight?: boolean }) => (
    <button
      onClick={() => selectFacility(f)}
      className={`card w-full text-left hover:shadow-md transition-all ${selected?.id === f.id ? 'ring-2 ring-primary-500' : ''} ${highlight ? 'border-primary-300 bg-primary-50/40' : ''}`}
    >
      <div className="flex items-start justify-between mb-2 gap-2">
        <h3 className="font-semibold text-gray-900 text-sm">{f.name}</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${
          f.facility_type === 'hospital' ? 'bg-red-100 text-red-700' :
          f.facility_type === 'phc' ? 'bg-green-100 text-green-700' :
          f.facility_type === 'chc' ? 'bg-blue-100 text-blue-700' :
          'bg-gray-100 text-gray-700'
        }`}>{f.facility_type}</span>
      </div>
      <p className="text-xs text-gray-600 mb-2">{f.address}</p>
      <div className="flex flex-wrap gap-1 mb-2">
        {(f.services || []).slice(0, 4).map((s: string, i: number) => (
          <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{s}</span>
        ))}
      </div>
      <div className="flex items-center gap-4 text-xs text-gray-500">
        {f.distance_km != null && (
          <span className="flex items-center gap-1 font-medium text-gray-700">
            <Navigation size={12} /> {formatDistance(f.distance_km)}
          </span>
        )}
        {f.contact_number && <span className="flex items-center gap-1"><Phone size={12} /> {f.contact_number}</span>}
        {f.opening_hours && <span className="flex items-center gap-1"><Clock size={12} /> {f.opening_hours}</span>}
      </div>
      {f.emergency_available && (
        <span className="mt-2 inline-block text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded font-medium">
          <Siren size={11} className="inline mr-1" />24/7 Emergency
        </span>
      )}
      <span className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary-600">
        <RouteIcon size={12} /> Show route
      </span>
    </button>
  );

  // ---------------- render ----------------

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <MapPin className="text-healthcare-600" size={22} /> Find Hospitals &amp; Care
          </h2>
          <p className="text-sm text-gray-500">
            {userPos
              ? 'Ranked from your location — tap any hospital to see the road route.'
              : 'Allow location access for precise nearby ranking, or browse all facilities.'}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {userPos && (
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium inline-flex items-center gap-1.5 ${
              locSource === 'gps' ? 'bg-green-100 text-green-700' :
              locSource === 'map' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
            }`}>
              <LocateFixed size={12} />
              {locSource === 'gps' ? 'GPS location' : locSource === 'map' ? 'Pinned on map' : 'Saved location'}
            </span>
          )}
          <button
            onClick={() => requestBrowserLocation(true)}
            disabled={locating}
            className="btn-secondary text-sm flex items-center gap-2 whitespace-nowrap"
          >
            <LocateFixed size={15} className={locating ? 'animate-pulse' : ''} />
            {locating ? 'Sensing…' : 'Use my location'}
          </button>
          <button
            onClick={() => { setPicking((p) => !p); setLocationNote(picking ? null : 'Tap the map where you are.'); }}
            className={`text-sm flex items-center gap-2 whitespace-nowrap px-3 py-2 rounded-lg border transition-colors ${
              picking ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <Crosshair size={15} /> {picking ? 'Cancel' : 'Set on map'}
          </button>
        </div>
      </div>

      {locationNote && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg p-3 flex items-start gap-2">
          <Navigation size={15} className="mt-0.5 shrink-0" /> {locationNote}
        </div>
      )}

      {/* Route panel (shows when a hospital is selected) */}
      {selected && (
        <div className="card border-primary-200 bg-primary-50/50">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <RouteIcon size={16} className="text-primary-600" /> Route to {selected.name}
              </h3>
              {routeLoading && (
                <p className="text-sm text-gray-500 mt-1">Finding the best road route…</p>
              )}
              {!routeLoading && route && (
                <div className="mt-2 flex flex-wrap items-center gap-4">
                  <span className="text-lg font-bold text-primary-700">{formatDistance(route.distance_km)}</span>
                  {route.duration_min > 0 && (
                    <span className="text-sm text-gray-600 flex items-center gap-1">
                      <Clock size={14} /> ≈ {formatDuration(route.duration_min)} by car
                    </span>
                  )}
                  {!route.steps.length && (
                    <span className="text-xs text-amber-600">(straight line — no road data)</span>
                  )}
                </div>
              )}
              {!routeLoading && routeError && (
                <p className="text-xs text-amber-700 mt-1">{routeError}</p>
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {selected.contact_number && (
                <a href={`tel:${selected.contact_number}`} className="btn-secondary text-sm flex items-center gap-1">
                  <Phone size={14} /> Call
                </a>
              )}
              <a
                href={`https://www.google.com/maps/dir/?api=1&origin=${userPos?.lat ?? ''},${userPos?.lon ?? ''}&destination=${selected.latitude},${selected.longitude}&travelmode=driving`}
                target="_blank"
                rel="noreferrer"
                className="btn-primary text-sm flex items-center gap-1"
              >
                <ExternalLink size={14} /> Navigate in Google Maps
              </a>
              <button onClick={clearRoute} className="p-1.5 text-gray-400 hover:text-gray-600" title="Close route">
                <X size={18} />
              </button>
            </div>
          </div>

          {route && route.steps.length > 0 && (
            <div className="mt-3 max-h-44 overflow-y-auto bg-white rounded-lg border border-gray-100 divide-y divide-gray-50">
              {route.steps.map((s, i) => (
                <div key={i} className="px-3 py-1.5 flex items-center gap-2 text-xs">
                  <span className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold shrink-0">{i + 1}</span>
                  <span className="flex-1 text-gray-700">{s.text}</span>
                  {s.distance_m > 0 && <span className="text-gray-400 whitespace-nowrap">{formatDistance(s.distance_m / 1000)}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Map */}
      <div className="card p-0 overflow-hidden relative">
        <div ref={mapDivRef} className="h-[420px] bg-gray-100 z-0" />
        {!mapReady && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            {loading ? <LoadingSpinner /> : <p className="text-gray-400">Preparing map…</p>}
          </div>
        )}
      </div>

      {/* Best hospitals */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-1 flex items-center gap-2">
            <Award size={17} className="text-primary-600" /> Best Hospitals Near You
          </h3>
          <p className="text-xs text-gray-500 mb-3">
            {bestMeta?.used_fallback
              ? `No hospitals within ${bestMeta.radius_km} km — showing the nearest hospitals anywhere, closest first.`
              : userPos
                ? `Closest hospitals to you (within ${bestMeta?.radius_km ?? 15} km) — nearest first, best-rated breaks ties.`
                : 'Get your location to rank hospitals near you.'}
          </p>
          {nearbyBest.length > 0 ? (
            <div className="space-y-3">
              {nearbyBest.map((f, i) => (
                <div key={f.id} className="relative">
                  <span className="absolute -left-1 -top-1 z-10 w-6 h-6 rounded-full bg-primary-600 text-white text-xs font-bold flex items-center justify-center shadow">#{i + 1}</span>
                  <FacilityCard f={f} highlight />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 py-3">
              {locating ? 'Sensing your location…' : 'Tap “Use my location” or “Set on map” to see hospitals closest to you.'}
            </p>
          )}
        </div>

        <div className="card">
          <h3 className="font-bold text-gray-900 mb-1 flex items-center gap-2">
            <Star size={17} className="text-amber-500" /> Best Hospitals Overall
          </h3>
          <p className="text-xs text-gray-500 mb-3">Region's top facilities by capability — services, emergency care, and 24/7 availability.</p>
          <div className="space-y-3">
            {overallBest.map((f, i) => (
              <div key={f.id} className="relative">
                <span className="absolute -left-1 -top-1 z-10 w-6 h-6 rounded-full bg-amber-500 text-white text-xs font-bold flex items-center justify-center shadow">#{i + 1}</span>
                <FacilityCard f={f} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters + full list */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
          <input type="text" className="input-field pl-9" placeholder="Search facilities..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
        </div>
        <div className="flex gap-2 flex-wrap">
          {['', 'hospital', 'phc', 'chc', 'clinic', 'pharmacy', 'diagnostic'].map((type) => (
            <button key={type} onClick={() => setFilter(type)} className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${filter === type ? 'bg-healthcare-600 text-white border-healthcare-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'}`}>
              {type || 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading facilities..." />
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {visibleFacilities.map((f) => (
            <FacilityCard key={f.id} f={f} />
          ))}
        </div>
      )}
    </div>
  );
}
