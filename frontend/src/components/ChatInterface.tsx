import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import StatusIndicator from './StatusIndicator';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';
import './ChatInterface.css';

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  metadata?: {
    confidence?: number;
    processing_time?: number;
    retrieved_chunks?: number;
  };
}

export interface ApiResponse {
  decision: string;
  reasoning: string;
  confidence: number;
  justification?: {
    clauses: Array<{
      text: string;
      source: string;
      section?: string;
      relevance_score: number;
    }>;
  };
  recommendations?: string[];
  query_understanding?: any;
  retrieved_chunks?: number;
  processing_time?: number;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ChatInterfaceProps {}

const ChatInterface: React.FC<ChatInterfaceProps> = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [documentTrigger, setDocumentTrigger] = useState(0);
  const [isDocumentListCollapsed, setIsDocumentListCollapsed] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [backendStatus, setBackendStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [documentsRefresh, setDocumentsRefresh] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkAPIHealth();
    const interval = setInterval(checkAPIHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // No welcome message - clean start
  }, []);

  const checkAPIHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
      setIsOnline(response.status === 200);
      setBackendStatus(response.data);
    } catch (error) {
      setIsOnline(false);
      setBackendStatus(null);
    }
  };

  const addMessage = (content: string, isUser: boolean, metadata?: any): void => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser,
      timestamp: new Date(),
      metadata
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const formatBotResponse = (data: ApiResponse): string => {
    let responseText = `${data.reasoning}\n\n`;
    
    if (data.justification && data.justification.clauses && data.justification.clauses.length > 0) {
      responseText += `**Source**: ${data.justification.clauses[0].source}`;
    }

    return responseText;
  };

  const handleSendMessage = async (query: string) => {
    if (!query.trim()) return;

    // Add user message
    addMessage(query, true);
    setIsLoading(true);

    if (!isOnline) {
      addMessage("❌ Backend is offline. Please make sure the API server is running on port 8000.", false);
      setIsLoading(false);
      return;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/process`, {
        query: query,
        use_llm_reasoning: true,
        top_k: 5,
        include_neighbors: true,
        neighbor_range: 1
      }, {
        timeout: 30000 // 30 second timeout
      });

      const data: ApiResponse = response.data;
      const formattedResponse = formatBotResponse(data);

      addMessage(formattedResponse, false);

    } catch (error) {
      console.error('Query processing failed:', error);
      if (axios.isAxiosError(error)) {
        if (error.response) {
          addMessage(`❌ Error: ${error.response.data?.detail || 'API request failed'}`, false);
        } else if (error.code === 'ECONNABORTED') {
          addMessage("❌ Request timeout. The query is taking too long to process.", false);
        } else {
          addMessage("❌ Network error. Please check your connection.", false);
        }
      } else {
        addMessage(`❌ Unexpected error: ${error}`, false);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleQuery = (query: string) => {
    handleSendMessage(query);
  };

  const handleUploadSuccess = (filename: string, chunks: number) => {
    const successMessage = `✅ **Document uploaded successfully!**

📄 **File**: ${filename}  
📊 **Processed**: ${chunks} text chunks created  
🔍 **Status**: Ready for queries  

You can now ask questions about this document!`;
    
    addMessage(successMessage, false);
    setDocumentsRefresh(prev => prev + 1); // Refresh document list
    setShowUpload(false); // Hide upload area after success
  };

  const handleUploadError = (error: string) => {
    const errorMessage = `❌ **Upload failed**

**Error**: ${error}

Please try again with a supported file format (PDF, DOCX, TXT) under 50MB.`;
    
    addMessage(errorMessage, false);
  };

  const handleDocumentDelete = (filename: string) => {
    const deleteMessage = `🗑️ **Document removed**

**File**: ${filename} has been deleted from the system.

The document is no longer available for queries.`;
    
    addMessage(deleteMessage, false);
    setDocumentsRefresh(prev => prev + 1); // Refresh document list
  };

  return (
    <div className="chat-interface">
      <StatusIndicator isOnline={isOnline} status={backendStatus} />
      
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <h1>🛡️ PolicyPilot Assistant</h1>
            <p>Ask questions about your insurance policies and claims</p>
          </div>
          <div className="header-actions">
            <button
              className={`upload-toggle-btn ${showUpload ? 'active' : ''}`}
              onClick={() => setShowUpload(!showUpload)}
              title="Upload Documents"
            >
              📄 {showUpload ? 'Hide Upload' : 'Upload Docs'}
            </button>
          </div>
        </div>

        {showUpload && (
          <div className="upload-section">
            <FileUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              disabled={isLoading || !isOnline}
              apiBaseUrl={API_BASE_URL}
            />
          </div>
        )}

        <DocumentList
          apiBaseUrl={API_BASE_URL}
          onDocumentDelete={handleDocumentDelete}
          refreshTrigger={documentsRefresh}
          isCollapsed={isDocumentListCollapsed}
          onToggleCollapse={() => setIsDocumentListCollapsed(!isDocumentListCollapsed)}
        />

        <MessageList 
          messages={messages}
          isLoading={isLoading}
          onExampleQuery={handleExampleQuery}
        />
        <div ref={messagesEndRef} />

        <ChatInput 
          onSendMessage={handleSendMessage}
          disabled={isLoading || !isOnline}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
