// File: frontend/src/components/SourcePanel/SourcePanel.tsx
// Purpose: Right sidebar showing document sources for answers

import React from 'react';
import { X, FileText, ExternalLink } from 'lucide-react';
import { Source } from '../../types';

interface SourcePanelProps {
  sources: Source[];
  isOpen: boolean;
  onClose: () => void;
  darkMode: boolean;
}

const SourcePanel: React.FC<SourcePanelProps> = ({ sources, isOpen, onClose, darkMode }) => {
  if (!isOpen) return null;

  return (
    <div className={`w-96 h-full flex flex-col ${darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} border-l`}>
      {/* Header */}
      <div className={`p-4 border-b flex items-center justify-between ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
        <h2 className={`text-lg font-semibold flex items-center space-x-2 ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>
          <FileText size={20} />
          <span>Sources</span>
        </h2>
        <button
          onClick={onClose}
          className={darkMode ? 'text-gray-500 hover:text-gray-300 transition-colors' : 'text-gray-400 hover:text-gray-600 transition-colors'}
        >
          <X size={20} />
        </button>
      </div>
      {/* Sources List */}
      <div className={`flex-1 overflow-y-auto p-4 ${darkMode ? 'bg-gray-900' : ''}`}>
        {sources.length === 0 ? (
          <div className="text-center py-8">
            <FileText size={48} className={darkMode ? 'text-gray-700 mx-auto mb-2' : 'text-gray-300 mx-auto mb-2'} />
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>No sources to display</p>
            <p className={`text-xs mt-1 ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>
              Click on source links in messages to view details
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {sources.map((source, index) => (
              <div 
                key={`${source.documentId}-${index}`}
                className={`rounded-lg p-4 border ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}
              >
                {/* Document header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <FileText size={16} className="text-primary" />
                    <h3 className={`font-medium text-sm ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>
                      {source.documentName}
                    </h3>
                  </div>
                  {source.pageNumber && (
                    <span className={`text-xs px-2 py-1 rounded ${darkMode ? 'bg-primary bg-opacity-20 text-primary' : 'bg-primary bg-opacity-10 text-primary'}`}>
                      Page {source.pageNumber}
                    </span>
                  )}
                </div>
                {/* Content chunk */}
                <div className={`rounded p-3 border ${darkMode ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <p className={`text-sm leading-relaxed ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    {source.chunk}
                  </p>
                </div>
                {/* Relevance score */}
                {source.relevanceScore && (
                  <div className="mt-2">
                    <div className={`flex items-center justify-between text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      <span>Relevance</span>
                      <span>{Math.round(source.relevanceScore * 100)}%</span>
                    </div>
                    <div className={`mt-1 h-2 rounded-full overflow-hidden ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                      <div 
                        className="h-full bg-primary transition-all duration-300"
                        style={{ width: `${source.relevanceScore * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      {/* Footer */}
      {sources.length > 0 && (
        <div className={`p-4 border-t ${darkMode ? 'border-gray-800 bg-gray-800' : 'border-gray-200 bg-gray-50'}`}>
          <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            Showing {sources.length} source{sources.length > 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
};

export default SourcePanel;