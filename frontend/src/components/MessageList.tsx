import React from 'react';
import { Message } from './ChatInterface';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  onExampleQuery: (query: string) => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, onExampleQuery }) => {
  const formatMessageContent = (content: string) => {
    // Convert markdown-style formatting to HTML
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  const exampleQueries = [
    "What are the exclusions in health insurance?",
    "46M, knee surgery, Mumbai, coverage amount?",
    "What are the maternity benefits?",
    "Waiting periods for pre-existing conditions?",
    "What dental treatments are covered?"
  ];

  return (
    <div className="message-list">
      {messages.length === 1 && (
        <div className="example-queries">
          <h3>💡 Try these example queries:</h3>
          <div className="example-query-buttons">
            {exampleQueries.map((query, index) => (
              <button
                key={index}
                className="example-query-button"
                onClick={() => onExampleQuery(query)}
                disabled={isLoading}
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((message) => (
        <div key={message.id} className={`message ${message.isUser ? 'message-user' : 'message-bot'}`}>
          <div className="message-content">
            <div 
              dangerouslySetInnerHTML={{ 
                __html: formatMessageContent(message.content) 
              }}
            />
            <div className="message-info">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              {message.metadata?.confidence && (
                <span> • Confidence: {Math.round(message.metadata.confidence * 100)}%</span>
              )}
              {message.metadata?.processing_time && (
                <span> • {message.metadata.processing_time.toFixed(1)}s</span>
              )}
              {message.metadata?.retrieved_chunks && (
                <span> • {message.metadata.retrieved_chunks} chunks</span>
              )}
            </div>
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="message message-bot">
          <div className="message-content">
            <div className="typing-indicator">
              <div className="typing-dots">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
