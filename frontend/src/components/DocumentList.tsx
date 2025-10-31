import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DocumentList.css';

interface Document {
  name: string;
  chunks: number;
  estimated_tokens?: number;
  size?: number;
  uploaded_at?: string;
}

interface DocumentListProps {
  apiBaseUrl: string;
  onDocumentDelete?: (filename: string) => void;
  refreshTrigger?: number;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  apiBaseUrl,
  onDocumentDelete,
  refreshTrigger,
  isCollapsed = false,
  onToggleCollapse
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${apiBaseUrl}/documents`);
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Failed to load documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [apiBaseUrl, refreshTrigger]);

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      await axios.delete(`${apiBaseUrl}/documents/${encodeURIComponent(filename)}`);
      await fetchDocuments(); // Refresh list
      onDocumentDelete?.(filename);
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Failed to delete document');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="document-list loading">
        <div className="spinner-small"></div>
        <span>Loading documents...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-list error">
        <span>⚠️ {error}</span>
        <button onClick={fetchDocuments} className="retry-btn">Retry</button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="document-list empty compact">
        <div className="document-list-header">
          <span className="empty-message">📄 No documents uploaded yet</span>
          {onToggleCollapse && (
            <button onClick={onToggleCollapse} className="collapse-btn" title="Hide">
              ➖
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`document-list ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="document-list-header" onClick={onToggleCollapse}>
        <h4>📚 Documents ({documents.length})</h4>
        <div className="header-actions">
          <button onClick={fetchDocuments} className="refresh-btn" title="Refresh">
            🔄
          </button>
          {onToggleCollapse && (
            <button onClick={onToggleCollapse} className="collapse-btn" title={isCollapsed ? "Show documents" : "Hide documents"}>
              {isCollapsed ? '➕' : '➖'}
            </button>
          )}
        </div>
      </div>
      
      {!isCollapsed && (
        <div className="documents">
          {documents.map((doc, index) => (
            <div key={index} className="document-item">
              <div className="document-info">
                <div className="document-name" title={doc.name}>
                  📄 {doc.name}
                </div>
                <div className="document-meta">
                  <span className="chunks">{doc.chunks} chunks</span>
                  {doc.estimated_tokens && (
                    <span className="tokens">~{(doc.estimated_tokens / 1000).toFixed(1)}k tokens</span>
                  )}
                  {doc.size && (
                    <span className="size">{formatFileSize(doc.size)}</span>
                  )}
                  {doc.uploaded_at && (
                    <span className="date">{formatDate(doc.uploaded_at)}</span>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(doc.name);
                }}
                className="delete-btn"
                title="Delete document"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentList;
