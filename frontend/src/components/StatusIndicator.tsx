import React from 'react';

interface StatusIndicatorProps {
  isOnline: boolean;
  status: any;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ isOnline, status }) => {
  return (
    <div className={`status-indicator ${isOnline ? 'status-online' : 'status-offline'}`}>
      <div className="status-dot"></div>
      <span className="status-text">
        {isOnline ? 'Backend Online' : 'Backend Offline'}
      </span>
      {status && isOnline && (
        <div className="status-details">
          <small>
            {status.documents?.total_documents || 0} docs, {status.documents?.total_chunks || 0} chunks
          </small>
        </div>
      )}
    </div>
  );
};

export default StatusIndicator;
