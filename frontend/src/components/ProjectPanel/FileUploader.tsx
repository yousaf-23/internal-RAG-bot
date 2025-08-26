// File: frontend/src/components/ProjectPanel/FileUploader.tsx
// Purpose: Drag-and-drop file upload component for documents

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File } from 'lucide-react';

interface FileUploaderProps {
  projectId: string;
  onFileUpload: (files: File[], projectId: string) => void;
  darkMode?: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ projectId, onFileUpload, darkMode }) => {
  // Handle file drop - useCallback prevents function recreation on each render
  const onDrop = useCallback((acceptedFiles: File[]) => {
    console.log('[FileUploader] Files dropped:', acceptedFiles.map(f => f.name));
    onFileUpload(acceptedFiles, projectId);
  }, [onFileUpload, projectId]);

  // Configure react-dropzone with file type restrictions
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: true  // Allow multiple file selection
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-4
        transition-all cursor-pointer
        ${isDragActive 
          ? (darkMode ? 'border-primary bg-primary bg-opacity-10' : 'border-primary bg-primary bg-opacity-5') 
          : (darkMode ? 'border-gray-700 hover:border-primary hover:bg-gray-800' : 'border-gray-300 hover:border-primary hover:bg-gray-50')
        }
        ${darkMode ? 'bg-gray-900' : ''}
      `}
    >
      <input {...getInputProps()} />
      <div className="text-center">
        <Upload 
          size={24} 
          className={`mx-auto mb-2 ${isDragActive ? 'text-primary' : (darkMode ? 'text-gray-500' : 'text-gray-400')}`}
        />
        <p className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
          {isDragActive 
            ? 'Drop files here...' 
            : 'Drag & drop files or click to browse'
          }
        </p>
        <p className={`text-xs mt-1 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
          PDF, Word, Excel files
        </p>
      </div>
    </div>
  );
};

export default FileUploader;