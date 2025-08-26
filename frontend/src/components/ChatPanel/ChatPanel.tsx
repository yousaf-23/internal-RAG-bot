// File: frontend/src/components/ChatPanel/ChatPanel.tsx
// Purpose: Central chat interface for document Q&A

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Moon, Sun } from 'lucide-react';
import { ChatMessage, Source } from '../../types';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import MessageBubble from './MessageBubble';
import { postChatQuery } from '../../services/useChat';

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  selectedProjectName?: string;
  selectedProjectId: string;
  onSendMessage: (message: string) => void;
  onSourceClick: (sources: Source[]) => void;
  setMessages: any
  setIsLoading:any
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isLoading,
  selectedProjectName,
  onSendMessage,
  onSourceClick,
  setMessages,
  setIsLoading,
  selectedProjectId,
  darkMode,
  onToggleDarkMode,
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage);
      const payload = {
        include_sources: true,
        max_chunks: process.env.REACT_APP_NUM_CHUNKS ? parseInt(process.env.REACT_APP_NUM_CHUNKS) : 5,
        project_id:selectedProjectId ,
        query: inputMessage
      }

      setInputMessage('');
      const response = await postChatQuery(payload);
      if (response.success) {
        const message = {
          id: response.conversation_id, 
          projectId: response.message_metadata.project_id, // Use project_id from message_metadata
          content: response.response, // Content from the response field
          role: 'assistant', // Role is set to 'assistant' since the response is from the assistant
          timestamp: response.message_metadata.timestamp, // Timestamp from message_metadata
          sources: response.sources // Optional sources, if available
        };
        setMessages((prevMessages: any) => [...prevMessages, message]);
        setInputMessage('');
        setIsLoading(false);
      } else {
        console.error('Failed to send message');
      }
      setIsLoading(false);
    }
  };
console.log("ChatPanel messages:", messages);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`flex-1 flex flex-col h-full ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
      {/* Header */}
      <div className={`p-4 border-b flex justify-between items-center ${darkMode ? 'border-gray-800 bg-gradient-to-r from-gray-900 to-gray-800' : 'border-gray-200 bg-gradient-to-r from-primary to-primary-dark'}`}>
        <div>
          <h2 className={`text-lg font-semibold flex items-center space-x-2 ${darkMode ? 'text-white' : 'text-white'}`}>
            <Bot size={24} />
            <span>Document Assistant</span>
            {selectedProjectName && (
              <span className="text-sm opacity-80">• {selectedProjectName}</span>
            )}
          </h2>
          <p className={`text-xs opacity-80 mt-1 ${darkMode ? 'text-gray-300' : 'text-white'}`}>
            Ask questions about your uploaded documents
          </p>
        </div>
        <Button
          variant={darkMode ? 'secondary' : 'outline'}
          size="small"
          onClick={onToggleDarkMode}
          className="ml-4"
          icon={darkMode ? <Sun size={16} /> : <Moon size={16} />}
        >
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </Button>
      </div>
      {/* Messages Area */}
      <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Bot size={64} className="mb-4" />
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm mt-2 text-center">
              {selectedProjectName
                ? `Start by asking a question about documents in "${selectedProjectName}"`
                : 'Select a project and upload documents to begin'}
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onSourceClick={onSourceClick}
                darkMode={darkMode}
              />
            ))}

            {isLoading && (
              <div className="flex items-start space-x-2">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <LoadingSpinner size="small" message="Analyzing documents..." />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      {/* Input Area */}
      <div className={`${darkMode ? 'border-t border-gray-800 bg-gray-900' : 'border-t border-gray-200'} p-4`}>
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={selectedProjectName
              ? "Ask a question about your documents..."
              : "Select a project first..."}
            className={`flex-1 px-4 py-2 border rounded-lg resize-none font-poppins focus:outline-none ${darkMode ? 'bg-gray-800 border-gray-700 text-white focus:border-primary' : 'border-gray-300 focus:border-primary'}`}
            rows={2}
            disabled={isLoading || !selectedProjectName}
          />
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={!inputMessage.trim() || isLoading || !selectedProjectName}
            loading={isLoading}
            icon={<Send size={18} />}
          >
            Send
          </Button>
        </div>
        <p className={`text-xs mt-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default ChatPanel;