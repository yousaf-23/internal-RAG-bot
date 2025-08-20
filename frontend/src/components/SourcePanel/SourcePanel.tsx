// File: frontend/src/components/SourcePanel/SourcePanel.tsx
// Purpose: Right sidebar showing document sources for answers

import React from 'react';
import { X, FileText, ExternalLink } from 'lucide-react';
import { Source } from '../../types';

interface SourcePanelProps {
  sources: Source[];
  isOpen: boolean;
  onClose: () => void;
}

const SourcePanel: React.FC<SourcePanelProps> = ({ sources, isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="w-96 bg-white border-l border-gray-200 h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
          <FileText size={20} />
          <span>Sources</span>
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto p-4">
        {sources.length === 0 ? (
          <div className="text-center py-8">
            <FileText size={48} className="text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">No sources to display</p>
            <p className="text-gray-400 text-xs mt-1">
              Click on source links in messages to view details
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {sources.map((source, index) => (
              <div 
                key={`${source.documentId}-${index}`}
                className="bg-gray-50 rounded-lg p-4 border border-gray-200"
              >
                {/* Document header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <FileText size={16} className="text-primary" />
                    <h3 className="font-medium text-sm text-gray-800">
                      {source.documentName}
                    </h3>
                  </div>
                  {source.pageNumber && (
                    <span className="text-xs bg-primary bg-opacity-10 text-primary px-2 py-1 rounded">
                      Page {source.pageNumber}
                    </span>
                  )}
                </div>

                {/* Content chunk */}
                <div className="bg-white rounded p-3 border border-gray-200">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {source.chunk}
                  </p>
                </div>

                {/* Relevance score */}
                {source.relevanceScore && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Relevance</span>
                      <span>{Math.round(source.relevanceScore * 100)}%</span>
                    </div>
                    <div className="mt-1 h-2 bg-gray-200 rounded-full overflow-hidden">
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
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-sm text-gray-600">
            Showing {sources.length} source{sources.length > 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
};

export default SourcePanel;