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
  const [loadError, setLoadError] = useState<string | null>(null);
  const [liveSearching, setLiveSearching] = useState(false);
  const [liveFacilities, setLiveFacilities] = useState<Facility[]>([]);
  const [liveNote, setLiveNote] = useState<string | null>(null);
  const [offlineMode, setOfflineMode] = useState(false);
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
  // Mirror for async callbacks that must see the latest merged live list.
  const liveFacilitiesRef = useRef<Facility[]>([]);
  useEffect(() => {
    liveFacilitiesRef.current = liveFacilities;
    // Fold newly sensed places into the visible list without a refetch.
    if (liveFacilities.length > 0) {
      setAllFacilities((prev) => mergeLive(liveFacilities, prev));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveFacilities]);
  // Latest bestMeta for the localStorage cache writer.
  const bestMetaRef = useRef<{ used_fallback: boolean; radius_km: number } | null>(null);
  useEffect(() => { bestMetaRef.current = bestMeta; }, [bestMeta]);

  // ---------------- data loading ----------------

  /**
   * Sense hospitals that actually exist around the user right now using the
   * OpenStreetMap Overpass API (no API key needed). Results are merged with
   * the seeded catalogue so local records win over live duplicates.
   */
  const overpassNearby = async (pos: { lat: number; lon: number }): Promise<Facility[]> => {
    const q = `[out:json][timeout:20];(
      node["amenity"~"^(hospital|clinic|doctors|pharmacy)$"](around:8000,${pos.lat},${pos.lon});
      way["amenity"~"^(hospital|clinic|doctors|pharmacy)$"](around:8000,${pos.lat},${pos.lon});
    );out center tags 60;`;
    const res = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `data=${encodeURIComponent(q)}`,
    });
    if (!res.ok) throw new Error('Overpass unavailable');
    const json = await res.json();
    const typeMap: Record<string, string> = {
      hospital: 'hospital', clinic: 'clinic', doctors: 'clinic', pharmacy: 'pharmacy',
    };
    const seen = new Set<string>();
    const out: Facility[] = [];
    for (const el of json.elements || []) {
      const tags = el.tags || {};
      const name = tags.name;
      if (!name || seen.has(name)) continue;
      seen.add(name);
      const lat = el.lat ?? el.center?.lat;
      const lon = el.lon ?? el.center?.lon;
      if (lat == null || lon == null) continue;
      const ftype = typeMap[tags.amenity] || 'clinic';
      const emergency =
        tags.emergency === 'yes' || /24\s*\/\s*7|24x7/i.test(tags.opening_hours || '');
      out.push({
        id: 100000 + (el.id % 900000), // synthetic id — never collides with seeds
        name,
        facility_type: ftype,
        latitude: lat,
        longitude: lon,
        address: [tags['addr:street'], tags['addr:city']].filter(Boolean).join(', ') || null,
        services: Object.keys(tags).filter((t) => t.startsWith('healthcare:')).map((t) => t.replace('healthcare:', '').replace(/_/g, ' ')),
        emergency_available: emergency,
        opening_hours: tags.opening_hours || null,
        contact_number: tags.phone || tags['contact:phone'] || null,
        distance_km: straightLineKm(pos, { latitude: lat, longitude: lon }),
      });
    }
    return out;
  };

  const mergeLive = (live: Facility[], base: Facility[]): Facility[] => {
    const names = new Set(base.map((f) => f.name.toLowerCase()));
    return [...base, ...live.filter((f) => !names.has(f.name.toLowerCase()))];
  };

  // Last-ranked hospital list survives reloads and offline starts.
  const BEST_CACHE_KEY = 'cr_last_best';
  const saveBestCache = (best: any) => {
    try {
      localStorage.setItem(BEST_CACHE_KEY, JSON.stringify({
        nearby_best: best.nearby_best || [],
        overall_best: best.overall_best || [],
        meta: bestMetaRef.current,
      }));
    } catch { /* storage full/blocked — non-fatal */ }
  };
  const readBestCache = (): any | null => {
    try {
      const raw = localStorage.getItem(BEST_CACHE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  };

  const loadFacilities = async (pos?: { lat: number; lon: number } | null) => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await api.getFacilities();
      let list: Facility[] = data.facilities || [];
      // The service worker flags cached responses served while offline.
      setOfflineMode(!!(data as any)?.__offline);

      // Best-hospitals ranking needs the caller's coordinates when available.
      if (pos) {
        // Live sensing runs in parallel with the ranked catalogue request.
        setLiveSearching(true);
        const bestP = api
          .getBestHospitals(pos.lat, pos.lon)
          .then((best: any) => {
            setNearbyBest(best.nearby_best || []);
            setOverallBest(best.overall_best || []);
            setBestMeta({ used_fallback: !!best.used_fallback, radius_km: best.radius_km || 15 });
            saveBestCache(best);
          })
          .catch(() => {
            // Offline (or backend down): fall back to the last-ranked list.
            const cached = readBestCache();
            if (cached) {
              setNearbyBest(cached.nearby_best || []);
              setOverallBest(cached.overall_best || []);
              setBestMeta(cached.meta || null);
            }
          });
        const liveP = overpassNearby(pos)
          .then((live) => {
            setLiveFacilities(live);
            if (live.length > 0) {
              setLiveNote(`${live.length} more healthcare places sensed live around you (OpenStreetMap) — merged into the ranking, list and map.`);
            }
            return live;
          })
          .catch(() => [] as Facility[])
          .finally(() => setLiveSearching(false));
        const [, live] = await Promise.allSettled([bestP, liveP]).then((rs) =>
          rs.map((r) => (r.status === 'fulfilled' ? r.value : []))
        );
        // Re-rank with live-sensed hospitals included so they compete with
        // the curated catalogue in “Best Hospitals Near You”.
        const liveHospitals = (live as Facility[]).filter((f) => f.facility_type === 'hospital');
        if (liveHospitals.length > 0) {
          try {
            const merged = await api.getBestHospitalsLive(pos.lat, pos.lon, liveHospitals);
            setNearbyBest(merged.nearby_best || []);
            setOverallBest(merged.overall_best || []);
            setBestMeta({ used_fallback: !!merged.used_fallback, radius_km: merged.radius_km || 15 });
            saveBestCache(merged);
          } catch { /* catalogue-only ranking already shown */ }
        }
      } else {
        const best = await api.getBestHospitals();
        setNearbyBest([]);
        setOverallBest(best.overall_best || []);
        setBestMeta(null);
      }
      setAllFacilities((prev) => mergeLive(liveFacilitiesRef.current, list));
    } catch (e: any) {
      console.error(e);
      setLoadError(e?.message || 'Could not load facilities.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    // All three start concurrently — the map and catalogue must never wait on
    // the profile request, and profile failure must not block anything.
    loadFacilities(null);
    api.getProfile()
      .then((p) => {
        if (cancelled) return;
        if (p?.latitude != null && p?.longitude != null) {
          const pos = { lat: p.latitude, lon: p.longitude };
          setUserPos(pos);
          loadFacilities(pos);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) requestBrowserLocation(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const requestBrowserLocation = (manual: boolean) => {
    if (!('geolocation' in navigator)) {
      if (manual) setLocationNote('Location is not supported on this device/browser. Use “Set on map” instead.');
      return;
    }
    setLocating(true);
    setLocationNote(null);

    // Watchdog: if the browser never resolves the permission prompt (common
    // in embedded browsers), neither geolocation callback fires and the
    // button would stay stuck on “Sensing…” forever.
    let settled = false;
    const watchdog = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      setLocating(false);
      setLocationNote('Location sensing timed out — using your saved location. Tap “Set on map” to adjust.');
    }, 12000);

    const finish = (fn: () => void) => {
      if (settled) return;
      settled = true;
      clearTimeout(watchdog);
      fn();
    };

    const opts: PositionOptions = { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 };
    navigator.geolocation.getCurrentPosition(
      (position) => {
        finish(() => {
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
        });
      },
      (firstErr) => {
        // High-accuracy fixes often fail indoors or on desktops — retry once
        // with low accuracy before giving up.
        navigator.geolocation.getCurrentPosition(
          (position) => {
            finish(() => {
              const pos = { lat: position.coords.latitude, lon: position.coords.longitude };
              setUserPos(pos);
              setLocSource('gps');
              setLocating(false);
              setLocationNote(`Using your approximate GPS location (±${Math.round(position.coords.accuracy)} m).`);
              loadFacilities(pos);
              mapRef.current?.setView([pos.lat, pos.lon], 12);
            });
          },
          () => {
            finish(() => {
              setLocating(false);
              setLocationNote(
                firstErr.code === firstErr.PERMISSION_DENIED
                  ? 'Location permission denied — using your saved home location. Tap “Set on map” to fine-tune it.'
                  : 'Could not sense your location — using your saved home location. Tap “Set on map” to correct it.'
              );
            });
          },
          { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }
        );
      },
      opts
    );
  };

  // ---------------- map ----------------

  useEffect(() => {
    // Initialize as soon as the catalogue attempt finishes — an empty result
    // must still produce a map, never a stuck “Preparing…” overlay.
    if (loading || mapReady || !mapDivRef.current) return;
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
  }, [loading]);

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
      const isLive = f.id >= 100000;
      const size = isBest ? 18 : 12;
      const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)${isLive ? ';opacity:0.85' : ''}"></div>`,
        iconSize: [size, size],
      });
      const marker = L.marker([f.latitude, f.longitude], { icon })
        .addTo(layer)
        .bindPopup(
          `<strong>${f.name}</strong>${isLive ? ' <span style="color:#2563eb">· live</span>' : ''}<br/>${formatDistance(f.distance_km)} · ${f.facility_type.toUpperCase()}<br/><small>${f.address || ''}</small>`
        );
      marker.on('click', () => selectFacility(f));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allFacilities, filter, searchQuery, nearbyBest, overallBest, mapReady, liveFacilities]);

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

      {loadError && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg p-3 flex items-center gap-3">
          <Siren size={15} className="shrink-0" />
          <span className="flex-1">{loadError}</span>
          <button onClick={() => loadFacilities(userPos)} className="btn-secondary text-xs whitespace-nowrap">Retry</button>
        </div>
      )}

      {locationNote && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg p-3 flex items-start gap-2">
          <Navigation size={15} className="mt-0.5 shrink-0" /> {locationNote}
        </div>
      )}

      {liveSearching && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 text-xs rounded-lg p-2.5 flex items-center gap-2">
          <LocateFixed size={13} className="animate-pulse" /> Sensing nearby healthcare places live from OpenStreetMap…
        </div>
      )}
      {!liveSearching && liveNote && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 text-xs rounded-lg p-2.5 flex items-start gap-2">
          <Award size={13} className="mt-0.5 shrink-0" /> {liveNote}
        </div>
      )}

      {offlineMode && (
        <div className="bg-gray-100 border border-gray-300 text-gray-700 text-xs rounded-lg p-2.5 flex items-start gap-2">
          <Siren size={13} className="mt-0.5 shrink-0" />
          <span>
            <strong>You're offline</strong> — showing your last-known hospitals and cached map tiles. Ranking may be out of date; routes and live sensing need a connection.
          </span>
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
              {locating
                ? 'Sensing your location…'
                : liveSearching
                  ? 'Searching for healthcare places around you…'
                  : 'Tap “Use my location” or “Set on map” to see hospitals closest to you.'}
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
      ) : visibleFacilities.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-gray-500 mb-2">No facilities match your search.</p>
          {loadError && <p className="text-sm text-red-600 mb-3">{loadError}</p>}
          <button onClick={() => loadFacilities(userPos)} className="btn-primary text-sm">Reload facilities</button>
        </div>
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
