import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import {
  Home, Activity, Brain, MapPin, AlertTriangle, FileText,
  Pill, Calendar, User, Heart, LogOut, Menu, X, Stethoscope
} from 'lucide-react';

const navItems = [
  { path: '/patient', label: 'Dashboard', icon: Home, exact: true },
  { path: '/patient/checkin', label: 'Health Check-in', icon: Activity },
  { path: '/patient/health-memory', label: 'Health Memory', icon: Heart },
  { path: '/patient/care-route', label: 'Find Care', icon: MapPin },
  { path: '/patient/documents', label: 'Documents', icon: FileText },
  { path: '/patient/medications', label: 'Medications', icon: Pill },
  { path: '/patient/prescriptions', label: 'Prescriptions', icon: Stethoscope },
  { path: '/patient/appointments', label: 'Appointments', icon: Calendar },
  { path: '/patient/profile', label: 'My Profile', icon: User },
];

export function PatientLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [upcomingCount, setUpcomingCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api.getAppointments()
      .then(d => {
        if (cancelled) return;
        const upcoming = (d.appointments || []).filter(
          (a: any) => a.status === 'scheduled' &&
            a.appointment_date && new Date(a.appointment_date) >= new Date()
        );
        setUpcomingCount(upcoming.length);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [location.pathname]);

  const isActive = (path: string, exact?: boolean) =>
    exact ? location.pathname === path : location.pathname.startsWith(path);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-64 bg-white border-r border-gray-200 transform transition-transform lg:transform-none ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="flex items-center gap-2 p-4 border-b">
          <Stethoscope className="text-primary-600" size={24} />
          <span className="font-bold text-primary-800">CareRoute AI</span>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>
        <nav className="p-3 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive(item.path, item.exact)
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <item.icon size={18} />
              {item.label}
              {item.label === 'Appointments' && upcomingCount > 0 && (
                <span
                  className="ml-auto bg-primary-600 text-white text-xs font-semibold px-2 py-0.5 rounded-full"
                  title={`${upcomingCount} upcoming appointment${upcomingCount > 1 ? 's' : ''}`}
                >
                  {upcomingCount}
                </span>
              )}
            </Link>
          ))}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t">
          <Link to="/patient" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 w-full">
            <AlertTriangle size={18} />
            Emergency Help
          </Link>
          <button onClick={() => { logout(); navigate('/'); }} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 w-full mt-1">
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 min-h-screen">
        <header className="sticky top-0 z-20 bg-white border-b px-4 py-3 flex items-center gap-4">
          <button className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <Menu size={24} />
          </button>
          <h1 className="font-semibold text-gray-900">Patient Dashboard</h1>
          <div className="ml-auto text-sm text-gray-500">
            Welcome, <span className="font-medium text-gray-900">{user?.full_name}</span>
          </div>
        </header>
        <main className="p-4 sm:p-6 max-w-7xl mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
