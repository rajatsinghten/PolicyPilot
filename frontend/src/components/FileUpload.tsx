import React, { useRef, useState } from 'react';
import axios from 'axios';
import './FileUpload.css';

interface FileUploadProps {
  onUploadSuccess: (filename: string, chunks: number) => void;
  onUploadError: (error: string) => void;
  disabled?: boolean;
  apiBaseUrl: string;
}

interface UploadResponse {
  message: string;
  filename: string;
  chunks_created: number;
  success: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  disabled = false,
  apiBaseUrl
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const supportedTypes = ['.pdf', '.docx', '.doc', '.txt'];
  const maxFileSize = 50 * 1024 * 1024; // 50MB

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    validateAndUpload(file);
  };

  const validateAndUpload = async (file: File) => {
    // Validate file type
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!supportedTypes.includes(fileExt)) {
      onUploadError(`Unsupported file type. Please upload: ${supportedTypes.join(', ')}`);
      return;
    }

    // Validate file size
    if (file.size > maxFileSize) {
      onUploadError(`File too large. Maximum size is ${maxFileSize / (1024 * 1024)}MB`);
      return;
    }

    // Upload file
    await uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post<UploadResponse>(
        `${apiBaseUrl}/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000, // 2 minute timeout for large files
        }
      );

      if (response.data.success) {
        onUploadSuccess(response.data.filename, response.data.chunks_created);
      } else {
        onUploadError(response.data.message || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          onUploadError('Upload timeout. The file may be too large or the connection is slow.');
        } else if (error.response) {
          onUploadError(error.response.data?.detail || 'Upload failed');
        } else {
          onUploadError('Network error during upload');
        }
      } else {
        onUploadError('Unexpected error during upload');
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="file-upload-container">
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => handleFileSelect(e.target.files)}
        accept={supportedTypes.join(',')}
        style={{ display: 'none' }}
        disabled={disabled || uploading}
      />
      
      <div
        className={`file-upload-zone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        {uploading ? (
          <div className="upload-status">
            <div className="spinner"></div>
            <span>Uploading and processing...</span>
          </div>
        ) : (
          <div className="upload-content">
            <div className="upload-icon">📄</div>
            <div className="upload-text">
              <strong>Upload Policy Document</strong>
              <p>Drop file here or click to browse</p>
              <small>Supports: {supportedTypes.join(', ')} (max {maxFileSize / (1024 * 1024)}MB)</small>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
