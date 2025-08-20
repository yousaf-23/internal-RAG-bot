// File: frontend/src/components/ChatPanel/MessageBubble.tsx
// Purpose: Individual message display component with source links

import React from 'react';
import { Bot, User, FileText } from 'lucide-react';
import { ChatMessage, Source } from '../../types';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: ChatMessage;
  onSourceClick: (sources: Source[]) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onSourceClick }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
        ${isUser ? 'bg-gray-600' : 'bg-primary'}
      `}>
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
      </div>

      {/* Message Content */}
      <div className={`max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`
          rounded-lg p-3
          ${isUser ? 'bg-gray-100' : 'bg-white border border-gray-200'}
        `}>
          {/* Render message - plain text for user, markdown for assistant */}
          {isUser ? (
            <p className="text-gray-800 font-poppins text-sm">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none font-poppins">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          
          {/* Source links for assistant messages */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => onSourceClick(message.sources!)}
                className="flex items-center space-x-1 text-xs text-primary hover:text-primary-dark transition-colors"
              >
                <FileText size={14} />
                <span>{message.sources.length} source{message.sources.length > 1 ? 's' : ''}</span>
              </button>
            </div>
          )}
        </div>
        
        {/* Timestamp */}
        <p className="text-xs text-gray-400 mt-1 px-1">
          {new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </p>
      </div>
    </div>
  );
};

export default MessageBubble;