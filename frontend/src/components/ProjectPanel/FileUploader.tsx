// File: frontend/src/components/ProjectPanel/FileUploader.tsx
// Purpose: Drag-and-drop file upload component for documents

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File } from 'lucide-react';

interface FileUploaderProps {
  projectId: string;
  onFileUpload: (files: File[], projectId: string) => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({ projectId, onFileUpload }) => {
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
          ? 'border-primary bg-primary bg-opacity-5' 
          : 'border-gray-300 hover:border-primary hover:bg-gray-50'
        }
      `}
    >
      <input {...getInputProps()} />
      <div className="text-center">
        <Upload 
          size={24} 
          className={`mx-auto mb-2 ${isDragActive ? 'text-primary' : 'text-gray-400'}`}
        />
        <p className="text-xs text-gray-600">
          {isDragActive 
            ? 'Drop files here...' 
            : 'Drag & drop files or click to browse'
          }
        </p>
        <p className="text-xs text-gray-400 mt-1">
          PDF, Word, Excel files
        </p>
      </div>
    </div>
  );
};

export default FileUploader;