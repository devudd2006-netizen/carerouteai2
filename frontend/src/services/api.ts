/**
 * CareRoute AI - API Service
 * Handles all backend communication with authentication and error handling.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('careroute_token');
  }

  async request<T = any>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;
    
    const token = this.getToken();
    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    };

    if (body && method !== 'GET') {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, config);
      
      if (response.status === 401) {
        localStorage.removeItem('careroute_token');
        localStorage.removeItem('careroute_user');
        window.location.href = '/login';
        throw new Error('Session expired. Please log in again.');
      }

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Request failed');
      }

      return data;
    } catch (error: any) {
      if (error.message === 'Failed to fetch') {
        throw new Error('Unable to connect to server. Please check if the backend is running.');
      }
      throw error;
    }
  }

  // Auth
  async register(data: any) { return this.request('/api/auth/register', { method: 'POST', body: data }); }
  async login(data: any) { return this.request('/api/auth/login', { method: 'POST', body: data }); }
  async getMe() { return this.request('/api/auth/me'); }
  async updateMe(data: any) { return this.request('/api/auth/me', { method: 'PUT', body: data }); }

  // Patient
  async getProfile() { return this.request('/api/patient/profile'); }
  async updateProfile(data: any) { return this.request('/api/patient/profile', { method: 'PUT', body: data }); }
  async getEmergencyContacts() { return this.request('/api/patient/emergency-contacts'); }
  async addEmergencyContact(data: any) { return this.request('/api/patient/emergency-contacts', { method: 'POST', body: data }); }

  // Health
  async createCheckin(data: any) { return this.request('/api/health/checkin', { method: 'POST', body: data }); }
  async getCheckins() { return this.request('/api/health/checkins'); }
  async getCheckin(id: number) { return this.request(`/api/health/checkins/${id}`); }
  async getTimeline() { return this.request('/api/health/timeline'); }
  async getAssessments() { return this.request('/api/health/assessments'); }
  async screenSymptoms(data: any) { return this.request('/api/health/screen', { method: 'POST', body: data }); }
  async getCareRoute(data: any) { return this.request('/api/health/care-route', { method: 'POST', body: data }); }

  // Documents
  async uploadDocument(formData: FormData) {
    const token = this.getToken();
    const response = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  }
  async getDocuments() { return this.request('/api/documents/'); }
  async getDocument(id: number) { return this.request(`/api/documents/${id}`); }

  // Prescriptions & Care Plans
  async getPrescriptions() { return this.request('/api/prescriptions'); }
  async createPrescription(data: any) { return this.request('/api/prescriptions', { method: 'POST', body: data }); }
  async confirmPrescription(id: number, data: any) { return this.request(`/api/prescriptions/${id}/confirm`, { method: 'POST', body: data }); }
  async getCarePlans() { return this.request('/api/care-plans'); }
  async createCarePlan(data: any) { return this.request('/api/care-plans', { method: 'POST', body: data }); }
  async getMedications() { return this.request('/api/medications'); }
  async logMedication(id: number, data: any) { return this.request(`/api/medications/${id}/taken`, { method: 'POST', body: data }); }
  async getAppointments() { return this.request('/api/appointments'); }
  async createAppointment(data: any) { return this.request('/api/appointments', { method: 'POST', body: data }); }

  // Facilities
  async getFacilities(params?: string) { return this.request(`/api/facilities/${params ? `?${params}` : ''}`); }
  async getNearbyFacilities(lat: number, lon: number, radius?: number) {
    return this.request(`/api/facilities/nearby?latitude=${lat}&longitude=${lon}&radius_km=${radius || 25}`);
  }
  async getFacility(id: number) { return this.request(`/api/facilities/${id}`); }

  // Emergency
  async evaluateEmergency(data: any) { return this.request('/api/emergency/evaluate', { method: 'POST', body: data }); }
  async generateHealthCard() { return this.request('/api/emergency/health-card', { method: 'POST', body: {} }); }
  async getSharedHealthCard(token: string) { return this.request(`/api/emergency/health-card/${token}`); }

  // Doctor
  async getDoctorPatients() { return this.request('/api/doctor/patients'); }
  async getDoctorPatient(id: number) { return this.request(`/api/doctor/patients/${id}`); }
  async addConsultation(data: any) { return this.request('/api/doctor/consultations', { method: 'POST', body: data }); }
  async createDoctorPrescription(data: any) { return this.request('/api/doctor/prescriptions', { method: 'POST', body: data }); }
  async createFollowup(data: any) { return this.request('/api/doctor/followups', { method: 'POST', body: data }); }

  // Community
  async getCommunityOverview() { return this.request('/api/community/overview'); }
  async getCommunityPriorityMap() { return this.request('/api/community/priority-map'); }
  async getCommunities() { return this.request('/api/community/communities'); }
  async getCommunityDetail(id: number) { return this.request(`/api/community/communities/${id}`); }
  async getCampRecommendations(data?: any) { return this.request('/api/community/camp-recommendation', { method: 'POST', body: data || {} }); }
  async listCampRecommendations() { return this.request('/api/community/camp-recommendations'); }

  // Admin
  async getAdminDashboard() { return this.request('/api/admin/dashboard'); }
  async getAdminUsers() { return this.request('/api/admin/users'); }
}

export const api = new ApiService();
