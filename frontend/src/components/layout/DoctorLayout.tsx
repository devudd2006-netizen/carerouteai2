import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Home, Users, Calendar, LogOut, Menu, Stethoscope } from 'lucide-react';

export function DoctorLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const isActive = (path: string, exact?: boolean) =>
    exact ? location.pathname === path : location.pathname.startsWith(path);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {sidebarOpen && <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />}
      <aside className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-64 bg-white border-r border-gray-200 transform transition-transform lg:transform-none ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="flex items-center gap-2 p-4 border-b">
          <Stethoscope className="text-primary-600" size={24} />
          <span className="font-bold text-primary-800">CareRoute AI</span>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>✕</button>
        </div>
        <nav className="p-3 space-y-1">
          <Link to="/doctor" onClick={() => setSidebarOpen(false)} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${isActive('/doctor', true) ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50'}`}>
            <Home size={18} /> Dashboard
          </Link>
          <Link to="/doctor" onClick={() => setSidebarOpen(false)} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${isActive('/doctor/patients') ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50'}`}>
            <Users size={18} /> My Patients
          </Link>
          <Link to="/doctor/appointments" onClick={() => setSidebarOpen(false)} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${isActive('/doctor/appointments') ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50'}`}>
            <Calendar size={18} /> Appointments
          </Link>
        </nav>
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t">
          <button onClick={() => { logout(); navigate('/'); }} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 w-full">
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </aside>
      <div className="flex-1 min-h-screen">
        <header className="sticky top-0 z-20 bg-white border-b px-4 py-3 flex items-center gap-4">
          <button className="lg:hidden" onClick={() => setSidebarOpen(true)}><Menu size={24} /></button>
          <h1 className="font-semibold text-gray-900">Doctor Dashboard</h1>
          <div className="ml-auto text-sm text-gray-500">
            Dr. <span className="font-medium text-gray-900">{user?.full_name}</span>
          </div>
        </header>
        <main className="p-4 sm:p-6 max-w-7xl mx-auto"><Outlet /></main>
      </div>
    </div>
  );
}
