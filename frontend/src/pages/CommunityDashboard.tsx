import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { BarChart3, MapPin, AlertTriangle, Users, TrendingUp, Heart, Tent, ArrowRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export function CommunityDashboard() {
  const [overview, setOverview] = useState<any>(null);
  const [priorityMap, setPriorityMap] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [ov, pm, rec] = await Promise.all([
        api.getCommunityOverview().catch(() => null),
        api.getCommunityPriorityMap().catch(() => ({ communities: [] })),
        api.listCampRecommendations().catch(() => ({ recommendations: [] })),
      ]);
      setOverview(ov);
      setPriorityMap(pm?.communities || []);
      setRecommendations(rec?.recommendations || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  if (loading) return <LoadingSpinner message="Analyzing community healthcare gaps..." />;

  const COLORS = ['#22c55e', '#eab308', '#f97316', '#dc2626'];
  const priorityData = overview?.priority_distribution ? [
    { name: 'Low', value: overview.priority_distribution.low || 0, color: COLORS[0] },
    { name: 'Medium', value: overview.priority_distribution.medium || 0, color: COLORS[1] },
    { name: 'High', value: overview.priority_distribution.high || 0, color: COLORS[2] },
    { name: 'Critical', value: overview.priority_distribution.critical || 0, color: COLORS[3] },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Heart className="text-red-500" size={22} /> Community Health Pulse
          </h2>
          <p className="text-sm text-gray-500">Healthcare accessibility analysis for communities</p>
        </div>
        <Link to="/community/map" className="btn-primary text-sm flex items-center gap-2">
          <MapPin size={14} /> View Gap Map <ArrowRight size={14} />
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: Users, label: 'Communities Monitored', value: overview?.communities_monitored || 0, color: 'primary' },
          { icon: AlertTriangle, label: 'High Priority Areas', value: overview?.high_priority_areas || 0, color: 'orange' },
          { icon: MapPin, label: 'Healthcare Gaps', value: overview?.healthcare_gaps || 0, color: 'red' },
          { icon: Tent, label: 'Recommended Camps', value: recommendations.length, color: 'healthcare' },
        ].map(({ icon: Icon, label, value, color }, i) => (
          <div key={i} className="card">
            <Icon className={`text-${color}-500 mb-2`} size={24} />
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Priority Distribution */}
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-4">Priority Distribution</h3>
          {priorityData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={priorityData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {priorityData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-500 text-center py-8">No data available</p>}
        </div>

        {/* Symptom Trends */}
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-4">Health Demand Trends</h3>
          {overview?.symptom_trends?.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={overview.symptom_trends.slice(0, 6)}>
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-500 text-center py-8">No trends available</p>}
        </div>
      </div>

      {/* Priority Communities Table */}
      <div className="card">
        <h3 className="font-bold text-gray-900 mb-4">Community Priority Scores</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 font-medium">Community</th>
                <th className="py-2 font-medium">District</th>
                <th className="py-2 font-medium">Population</th>
                <th className="py-2 font-medium">Distance to Facility</th>
                <th className="py-2 font-medium">Priority Score</th>
                <th className="py-2 font-medium">Level</th>
              </tr>
            </thead>
            <tbody>
              {priorityMap.slice(0, 10).map((c: any) => (
                <tr key={c.community_id} className="border-b hover:bg-gray-50">
                  <td className="py-2 font-medium">{c.community_name}</td>
                  <td className="py-2 text-gray-600">{c.district}</td>
                  <td className="py-2 text-gray-600">{c.population?.toLocaleString()}</td>
                  <td className="py-2 text-gray-600">{c.distance_score ? `${(c.distance_score / 100 * 30).toFixed(0)} km` : 'N/A'}</td>
                  <td className="py-2 font-semibold">{c.priority_score}</td>
                  <td className="py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      c.priority_level === 'critical' ? 'bg-red-100 text-red-700' :
                      c.priority_level === 'high' ? 'bg-orange-100 text-orange-700' :
                      c.priority_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>{c.priority_level}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Camp Recommendations */}
      {recommendations.length > 0 && (
        <div className="card">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Tent size={18} /> Medical Camp Recommendations
          </h3>
          <div className="space-y-3">
            {recommendations.map((r: any) => (
              <div key={r.id} className="p-4 bg-primary-50 rounded-lg border border-primary-100">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-gray-900">📍 {r.recommended_location}</h4>
                  <span className="text-sm font-bold text-primary-700">Score: {r.priority_score}</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{r.reason}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {(r.suggested_services || []).map((s: string, i: number) => (
                    <span key={i} className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">{s}</span>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Population: ~{r.population_affected?.toLocaleString()} • Duration: {r.suggested_duration_days} days
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-700">
        ⚠️ This is a decision-support system. Final deployment decisions remain with healthcare authorities.
        Community data is aggregated and de-identified to protect individual patient privacy.
      </div>
    </div>
  );
}
