import React, { useState } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
  isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="chat-input-container">
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          className="chat-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about your insurance policy..."
          disabled={disabled}
          rows={1}
          style={{ 
            resize: 'none',
            height: message.split('\n').length > 1 ? 'auto' : '44px',
            minHeight: '44px',
            maxHeight: '120px'
          }}
        />
        <button
          type="submit"
          className="send-button"
          disabled={disabled || !message.trim()}
        >
          {isLoading ? (
            <span className="loading-spinner">⏳</span>
          ) : (
            'Send'
          )}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
