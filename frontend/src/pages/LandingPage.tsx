import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, MapPin, Shield, Brain, Users, Activity, ArrowRight, Stethoscope, Zap } from 'lucide-react';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Stethoscope className="text-primary-600" size={28} />
            <span className="text-xl font-bold text-gray-900">CareRoute <span className="text-primary-600">AI</span></span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 px-3 py-2">Sign In</Link>
            <Link to="/register" className="btn-primary text-sm">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-healthcare-50" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-20 sm:py-32">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-primary-100 text-primary-800 text-sm font-medium px-3 py-1 rounded-full mb-6">
              <Zap size={14} /> AI-Powered Healthcare
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
              CARE ROUTE <span className="text-primary-600">AI</span>
            </h1>
            <p className="text-xl sm:text-2xl text-primary-700 font-medium mb-4">
              Your Digital Home Health Companion
            </p>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl leading-relaxed">
              An AI-assisted digital home healthcare platform connecting patients, doctors, emergency support and community healthcare — designed for rural and underserved communities.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/register" className="btn-primary text-lg px-8 py-3 inline-flex items-center gap-2 justify-center">
                Start Health Check <ArrowRight size={20} />
              </Link>
              <Link to="/login" className="btn-secondary text-lg px-8 py-3 inline-flex items-center gap-2 justify-center">
                Explore CareRoute
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Two-way flow */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Two-Way Healthcare Bridge</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">CareRoute AI works in two directions — helping patients reach care, and helping healthcare reach communities.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="card border-primary-200 bg-primary-50/50">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center"><Heart className="text-primary-600" size={20} /></div>
                <h3 className="text-xl font-bold text-primary-800">Patient → Healthcare</h3>
              </div>
              <p className="text-gray-600 mb-4 font-medium">"I need care. Help me reach the right care."</p>
              <div className="space-y-2 text-sm text-gray-600">
                {['Home Health Monitoring', 'AI-Assisted Preliminary Screening', 'Risk & Urgency Assessment', 'Care Route to Appropriate Facility', 'Doctor-Approved Care Plan', 'Continuous Monitoring & Follow-up'].map((item, i) => (
                  <div key={i} className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-primary-500" />{item}</div>
                ))}
              </div>
            </div>
            <div className="card border-healthcare-200 bg-healthcare-50/50">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-healthcare-100 flex items-center justify-center"><Users className="text-healthcare-600" size={20} /></div>
                <h3 className="text-xl font-bold text-healthcare-800">Healthcare → Community</h3>
              </div>
              <p className="text-gray-600 mb-4 font-medium">"This community needs healthcare. Help us decide where to send it."</p>
              <div className="space-y-2 text-sm text-gray-600">
                {['Community Health Data Aggregation', 'Healthcare Accessibility Analysis', 'Care Priority Scoring', 'Healthcare Gap Mapping', 'Mobile Medical Camp Recommendations', 'Community Health Intelligence'].map((item, i) => (
                  <div key={i} className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-healthcare-500" />{item}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Core Features</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { icon: Brain, title: 'AI Health Screening', desc: 'Preliminary symptom analysis with urgency assessment and care routing recommendations.' },
              { icon: MapPin, title: 'Care Route Engine', desc: 'Finds the right healthcare facility based on symptoms, urgency, distance, and capabilities.' },
              { icon: Heart, title: 'Health Memory', desc: 'Your complete longitudinal health profile — check-ins, records, prescriptions, all in one place.' },
              { icon: Shield, title: 'Emergency Detection', desc: 'Potentially serious symptom detection with emergency escalation and health card generation.' },
              { icon: Activity, title: 'Health Check-in', desc: 'Simple, conversational daily health monitoring designed for rural accessibility.' },
              { icon: Users, title: 'Community Health Pulse', desc: 'Aggregated healthcare analytics for community health planning and gap identification.' },
            ].map((feature, i) => (
              <div key={i} className="card hover:shadow-md transition-shadow">
                <feature.icon className="text-primary-600 mb-3" size={28} />
                <h3 className="font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Important Notice */}
      <section className="py-12 bg-yellow-50 border-y border-yellow-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h3 className="font-bold text-yellow-800 mb-2">Important Medical Safety Notice</h3>
          <p className="text-sm text-yellow-700">CareRoute AI provides preliminary health screening and care navigation support. It does NOT replace professional medical advice, diagnosis, or treatment. All AI outputs are labeled as preliminary screening. Always consult a qualified healthcare provider for medical decisions.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-gray-900 text-gray-400 text-center text-sm">
        <p>CareRoute AI — From your home to the right care.</p>
        <p className="mt-1">AI-assisted healthcare accessibility for rural and underserved communities.</p>
      </footer>
    </div>
  );
}
