// File: frontend/src/components/ChatPanel/MessageBubble.tsx
// Purpose: Individual message display component with source links

import React from 'react';
import { Bot, User, FileText } from 'lucide-react';
import { ChatMessage, Source } from '../../types';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: ChatMessage;
  onSourceClick: (sources: Source[]) => void;
  darkMode: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onSourceClick, darkMode }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
        ${isUser ? (darkMode ? 'bg-gray-700' : 'bg-gray-600') : (darkMode ? 'bg-primary' : 'bg-primary')}
      `}>
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
      </div>

      {/* Message Content */}
      <div className={`max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`
          rounded-lg p-3
          ${isUser 
            ? (darkMode ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-800') 
            : (darkMode ? 'bg-gray-900 border border-gray-700 text-white' : 'bg-white border border-gray-200 text-gray-800')
          }
        `}>
          {/* Render message - plain text for user, markdown for assistant */}
          {isUser ? (
            <p className={`font-poppins text-sm ${darkMode ? 'text-white' : 'text-gray-800'}`}>{message.content}</p>
          ) : (
            <div className={`prose prose-sm max-w-none font-poppins ${darkMode ? 'prose-invert' : ''}`}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          
          {/* Source links for assistant messages */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className={`mt-3 pt-3 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
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
        <p className={`text-xs mt-1 px-1 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
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