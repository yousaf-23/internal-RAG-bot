// File: frontend/src/components/ProjectPanel/ProjectPanel.tsx
// Purpose: Left sidebar for project management and file uploads

import React, { useState } from 'react';
import { Plus, Folder, Upload, Trash2, FileText } from 'lucide-react';
import { Project, Document } from '../../types';
import Button from '../common/Button';
import FileUploader from './FileUploader';

interface ProjectPanelProps {
  projects: Project[];
  selectedProject: Project | null;
  documents: Document[];
  onProjectSelect: (project: Project) => void;
  onProjectCreate: (name: string, description?: string) => void;
  onProjectDelete: (projectId: string) => void;
  onFileUpload: (files: File[], projectId: string) => void;
}

const ProjectPanel: React.FC<ProjectPanelProps> = ({
  projects,
  selectedProject,
  documents,
  onProjectSelect,
  onProjectCreate,
  onProjectDelete,
  onFileUpload
}) => {
  // Local state for the new project form
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  // Handle project creation
  const handleCreateProject = () => {
    if (newProjectName.trim()) {
      onProjectCreate(newProjectName, newProjectDescription);
      // Reset form
      setNewProjectName('');
      setNewProjectDescription('');
      setIsCreatingProject(false);
    }
  };

  // Filter documents for selected project
  const projectDocuments = selectedProject 
    ? documents.filter(doc => doc.projectId === selectedProject.id)
    : [];

  return (
    <div className="w-80 bg-white border-r border-gray-200 h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Projects</h2>
        
        <Button
          variant="primary"
          size="small"
          icon={<Plus size={16} />}
          onClick={() => setIsCreatingProject(true)}
          className="w-full"
        >
          New Project
        </Button>
      </div>

      {/* Project Creation Form */}
      {isCreatingProject && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <input
            type="text"
            placeholder="Project name"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md mb-2 font-poppins focus:outline-none focus:border-primary"
            autoFocus
          />
          <textarea
            placeholder="Description (optional)"
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md mb-2 font-poppins resize-none focus:outline-none focus:border-primary"
            rows={2}
          />
          <div className="flex space-x-2">
            <Button
              variant="primary"
              size="small"
              onClick={handleCreateProject}
              className="flex-1"
            >
              Create
            </Button>
            <Button
              variant="outline"
              size="small"
              onClick={() => {
                setIsCreatingProject(false);
                setNewProjectName('');
                setNewProjectDescription('');
              }}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => onProjectSelect(project)}
              className={`
                p-3 rounded-lg cursor-pointer transition-all
                ${selectedProject?.id === project.id 
                  ? 'bg-primary bg-opacity-10 border border-primary' 
                  : 'hover:bg-gray-50 border border-transparent'
                }
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Folder 
                    size={18} 
                    className={selectedProject?.id === project.id ? 'text-primary' : 'text-gray-500'}
                  />
                  <span className="font-medium text-gray-800">{project.name}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent project selection when deleting
                    onProjectDelete(project.id);
                  }}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              {project.description && (
                <p className="text-xs text-gray-500 mt-1 ml-6">{project.description}</p>
              )}
              <p className="text-xs text-gray-400 mt-1 ml-6">
                {project.fileCount} file{project.fileCount !== 1 ? 's' : ''}
              </p>
            </div>
          ))}
        </div>

        {/* Empty state */}
        {projects.length === 0 && (
          <div className="text-center py-8">
            <Folder size={48} className="text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">No projects yet</p>
            <p className="text-gray-400 text-xs mt-1">Create your first project to get started</p>
          </div>
        )}
      </div>

      {/* File Upload Section - Only show when project is selected */}
      {selectedProject && (
        <div className="border-t border-gray-200 p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Files in {selectedProject.name}
          </h3>
          
          <FileUploader
            projectId={selectedProject.id}
            onFileUpload={onFileUpload}
          />

          {/* Documents List */}
          {projectDocuments.length > 0 && (
            <div className="mt-3 max-h-40 overflow-y-auto">
              {projectDocuments.map((doc) => (
                <div key={doc.id} className="flex items-center space-x-2 py-1">
                  <FileText size={14} className="text-gray-400" />
                  <span className="text-xs text-gray-600 truncate flex-1">{doc.filename}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    doc.status === 'ready' ? 'bg-green-100 text-green-600' :
                    doc.status === 'processing' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-red-100 text-red-600'
                  }`}>
                    {doc.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectPanel;