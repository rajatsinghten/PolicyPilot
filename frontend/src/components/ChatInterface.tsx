import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import StatusIndicator from './StatusIndicator';
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

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [backendStatus, setBackendStatus] = useState<any>(null);
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
    // Add welcome message
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `👋 **Welcome to PolicyPilot Assistant!**

I'm your AI-powered insurance policy assistant with **enhanced context retrieval**. 

🔍 **What I can do:**
- Analyze your insurance policies with comprehensive context
- Find relevant coverage information with surrounding details
- Answer questions about claims, exclusions, and benefits
- Provide enhanced results using neighboring document sections

🚀 **Enhanced Features:**
- **Context-Aware Search**: When I find relevant information, I also include surrounding text for complete context
- **Comprehensive Coverage**: Get fuller answers with related policy sections
- **Smart Document Analysis**: AI-powered understanding of insurance terminology

💡 **Try asking:**
- "What dental treatments are covered?"
- "What are the exclusions for pre-existing conditions?"
- "What's the coverage for emergency procedures?"

Upload your policy documents via the backend API, then ask me anything! I'll provide detailed, contextual answers.`,
      isUser: false,
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
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
    let responseText = `**Decision**: ${data.decision}\n\n`;
    
    if (data.reasoning) {
      responseText += `**Analysis**: ${data.reasoning}\n\n`;
    }

    if (data.justification && data.justification.clauses && data.justification.clauses.length > 0) {
      responseText += `**📄 Relevant Policy Information** (with neighboring context):\n\n`;
      data.justification.clauses.forEach((clause, index) => {
        const preview = clause.text.length > 300 ? 
          clause.text.substring(0, 300) + "..." : 
          clause.text;
        
        responseText += `**${index + 1}. ${clause.source}** - *${clause.section || 'Section Unknown'}*\n`;
        responseText += `📊 **Relevance**: ${Math.round(clause.relevance_score * 100)}%\n\n`;
        responseText += `${preview}\n\n`;
        responseText += `---\n\n`;
      });
    }

    if (data.recommendations && data.recommendations.length > 0) {
      responseText += `**💡 Recommendations**:\n`;
      data.recommendations.forEach((rec, index) => {
        responseText += `${index + 1}. ${rec}\n`;
      });
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
        use_llm_reasoning: false,
        top_k: 5,
        include_neighbors: true,
        neighbor_range: 1
      }, {
        timeout: 30000 // 30 second timeout
      });

      const data: ApiResponse = response.data;
      const formattedResponse = formatBotResponse(data);

      addMessage(formattedResponse, false, {
        confidence: data.confidence,
        processing_time: data.processing_time || 0,
        retrieved_chunks: data.retrieved_chunks || 0
      });

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

  return (
    <div className="chat-interface">
      <StatusIndicator isOnline={isOnline} status={backendStatus} />
      
      <div className="chat-container">
        <div className="chat-header">
          <h1>🛡️ PolicyPilot Assistant</h1>
          <p>Ask questions about your insurance policies and claims</p>
        </div>

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
