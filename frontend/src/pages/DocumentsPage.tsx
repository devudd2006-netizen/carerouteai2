import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { FileText, Upload, Trash2, Eye, Calendar } from 'lucide-react';

export function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({ title: '', document_type: 'lab_report', doctor_name: '', facility_name: '' });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => { loadDocuments(); }, []);

  const loadDocuments = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data.documents || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', selectedFile);
      fd.append('title', formData.title || selectedFile.name);
      fd.append('document_type', formData.document_type);
      fd.append('doctor_name', formData.doctor_name);
      fd.append('facility_name', formData.facility_name);
      await api.uploadDocument(fd);
      setSelectedFile(null);
      setFormData({ title: '', document_type: 'lab_report', doctor_name: '', facility_name: '' });
      loadDocuments();
    } catch (e: any) {
      alert('Upload failed: ' + e.message);
    } finally { setUploading(false); }
  };

  const docTypeColors: Record<string, string> = {
    prescription: 'bg-purple-100 text-purple-700',
    lab_report: 'bg-blue-100 text-blue-700',
    scan: 'bg-green-100 text-green-700',
    discharge_summary: 'bg-orange-100 text-orange-700',
    certificate: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
        <FileText className="text-blue-500" size={22} /> Medical Documents
      </h2>

      {/* Upload Form */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Upload Document</h3>
        <form onSubmit={handleUpload} className="space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <input type="text" className="input-field" placeholder="Document title" value={formData.title} onChange={e => setFormData(f => ({ ...f, title: e.target.value }))} />
            <select className="input-field" value={formData.document_type} onChange={e => setFormData(f => ({ ...f, document_type: e.target.value }))}>
              <option value="prescription">Prescription</option>
              <option value="lab_report">Lab Report</option>
              <option value="scan">Scan / Image</option>
              <option value="discharge_summary">Discharge Summary</option>
              <option value="certificate">Medical Certificate</option>
            </select>
            <input type="text" className="input-field" placeholder="Doctor name (optional)" value={formData.doctor_name} onChange={e => setFormData(f => ({ ...f, doctor_name: e.target.value }))} />
            <input type="text" className="input-field" placeholder="Facility name (optional)" value={formData.facility_name} onChange={e => setFormData(f => ({ ...f, facility_name: e.target.value }))} />
          </div>
          <div className="flex items-center gap-3">
            <input type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt" onChange={e => setSelectedFile(e.target.files?.[0] || null)} className="text-sm text-gray-500" />
            <button type="submit" className="btn-primary text-sm flex items-center gap-2" disabled={!selectedFile || uploading}>
              <Upload size={14} /> {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>

      {/* Document List */}
      {loading ? <LoadingSpinner /> : documents.length === 0 ? (
        <EmptyState title="No documents yet" description="Upload prescriptions, lab reports, scans, or other medical documents." />
      ) : (
        <div className="space-y-3">
          {documents.map(doc => (
            <div key={doc.id} className="card flex items-center gap-4 hover:shadow-md transition-shadow">
              <FileText className="text-blue-500 flex-shrink-0" size={24} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900 truncate">{doc.title}</h4>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${docTypeColors[doc.document_type] || 'bg-gray-100 text-gray-700'}`}>
                    {doc.document_type.replace('_', ' ')}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mt-1 flex gap-3">
                  {doc.doctor_name && <span>Dr: {doc.doctor_name}</span>}
                  {doc.facility_name && <span>{doc.facility_name}</span>}
                  {doc.document_date && <span><Calendar size={10} className="inline" /> {doc.document_date}</span>}
                  {doc.created_at && <span>Uploaded: {new Date(doc.created_at).toLocaleDateString()}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
