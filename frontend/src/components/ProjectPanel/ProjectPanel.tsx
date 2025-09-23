// File: frontend/src/components/ProjectPanel/ProjectPanel.tsx
// Purpose: Left sidebar for project management and file uploads

import React, { use, useState , useEffect} from 'react';
import { Plus, Folder, Upload, Trash2, FileText } from 'lucide-react';
import { Project, Document } from '../../types';
import Button from '../common/Button';
import FileUploader from './FileUploader';
import { AddProjects, getProjectsQuery } from '../../services/useProjects';
import { deleteDocument } from '../../services/useProjectDocuments';

interface ProjectPanelProps {
  projects: Project[];
  selectedProject: Project | null;
  documents: Document[];
  onProjectSelect: (project: Project) => void;
  onProjectCreate: (name: string, description?: string) => void;
  onProjectDelete: (projectId: string) => void;
  onFileUpload: (files: File[], projectId: string) => void;
  fetchProjects: () => void;
  handleDeleteDocument: (documentId: string , projectId:string) => void;
  darkMode: boolean;
}

const ProjectPanel: React.FC<ProjectPanelProps> = ({
  projects,
  selectedProject,
  documents,
  onProjectSelect,
  onProjectCreate,
  onProjectDelete,
  onFileUpload,
  fetchProjects,
  handleDeleteDocument,
  darkMode
}) => {

  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    description: ''
  });


  const handleCreateProject = async() => {
    if (newProject.name.trim()) {
      // onProjectCreate(newProject.name, newProject.description);
      const response = await AddProjects(newProject);
      if (response) {
        console.log('Project created successfully:', response);
        fetchProjects(); 
      }
      setNewProject({ name: '', description: '' });
      setIsCreatingProject(false);
    }
  };


  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewProject(prevState => ({
      ...prevState,
      [name]: value
    }));
  };



  return (
    <div className={`w-80 h-full flex flex-col ${darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} border-r`}>
      {/* Header */}
      <div className={`p-4 border-b ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
        <h2 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>Projects</h2>
        <Button
          variant={darkMode ? 'secondary' : 'primary'}
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
        <div className={`p-4 ${darkMode ? 'bg-gray-800 border-gray-800' : 'bg-gray-50 border-gray-200'} border-b`}>
          <input
            type="text"
            placeholder="Project name"
            name="name"
            value={newProject.name}
            onChange={handleInputChange}
            className={`w-full px-3 py-2 border rounded-md mb-2 font-poppins focus:outline-none ${darkMode ? 'bg-gray-900 border-gray-700 text-white focus:border-primary' : 'border-gray-300 focus:border-primary'}`}
            autoFocus
          />
          <textarea
            placeholder="Description (optional)"
            name="description"
            value={newProject.description}
            onChange={handleInputChange}
            className={`w-full px-3 py-2 border rounded-md mb-2 font-poppins resize-none focus:outline-none ${darkMode ? 'bg-gray-900 border-gray-700 text-white focus:border-primary' : 'border-gray-300 focus:border-primary'}`}
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
                setNewProject({ name: '', description: '' });
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
                  ? (darkMode ? 'bg-primary bg-opacity-10 border border-primary' : 'bg-primary bg-opacity-10 border border-primary')
                  : (darkMode ? 'hover:bg-gray-800 border border-transparent' : 'hover:bg-gray-50 border border-transparent')
                }
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Folder 
                    size={18} 
                    className={selectedProject?.id === project.id ? 'text-primary' : (darkMode ? 'text-gray-400' : 'text-gray-500')} 
                  />
                  <span className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>{project.name}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent project selection when deleting
                    onProjectDelete(project.id);
                  }}
                  className={`transition-colors ${darkMode ? 'text-gray-500 hover:text-red-500' : 'text-gray-400 hover:text-red-500'}`}
                >
                  <Trash2 size={16} />
                </button>
              </div>
              {project.description && (
                <p className={`text-xs mt-1 ml-6 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{project.description}</p>
              )}
              <p className={`text-xs mt-1 ml-6 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                {project.file_count} file{project.file_count !== 1 ? 's' : ''}
              </p>
            </div>
          ))}
        </div>

        {/* Empty state */}
        {projects.length === 0 && (
          <div className="text-center py-8">
            <Folder size={48} className={`mx-auto mb-2 ${darkMode ? 'text-gray-700' : 'text-gray-300'}`} />
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>No projects yet</p>
            <p className={`text-xs mt-1 ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>Create your first project to get started</p>
          </div>
        )}
      </div>

      {/* File Upload Section - Only show when project is selected */}
      {selectedProject && (
        <div className={`p-4 border-t ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
          <h3 className={`text-sm font-semibold mb-3 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
            Files in {selectedProject.name}
          </h3>
          <FileUploader
            projectId={selectedProject.id}
            onFileUpload={onFileUpload}
            darkMode={darkMode}
          />
          {/* Documents List */}
          {documents.length > 0 && (
            <div className="mt-3 max-h-40 overflow-y-auto">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center space-x-2 py-1">
                  <FileText size={14} className={darkMode ? 'text-gray-600' : 'text-gray-400'} />
                  <span className={`text-xs truncate flex-1 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{doc.filename}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    doc.status === 'ready' ? (darkMode ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-600') :
                    doc.status === 'processing' ? (darkMode ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-100 text-yellow-600') :
                    (darkMode ? 'bg-red-900 text-red-300' : 'bg-red-100 text-red-600')
                  }`}>
                    {doc.status}
                  </span>
                    <button
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent project selection when deleting
                     handleDeleteDocument(doc.id , selectedProject.id);
                  }}
                  className={`transition-colors ${darkMode ? 'text-gray-500 hover:text-red-500' : 'text-gray-400 hover:text-red-500'}`}
                >
                  <Trash2 size={16} />
                </button>
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