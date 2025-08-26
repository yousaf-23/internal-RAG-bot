// File: frontend/src/App.tsx
// Purpose: Main application component that orchestrates all panels

import React, { useState, useCallback, useEffect } from 'react';
import './App.css';
import ProjectPanel from './components/ProjectPanel/ProjectPanel';
import ChatPanel from './components/ChatPanel/ChatPanel';
import SourcePanel from './components/SourcePanel/SourcePanel';
import { Project, Document, ChatMessage, Source } from './types';
import { getProjectsQuery, DeleteProjects } from './services/useProjects';
import { getProjectDocumentsQuery , uploadDocumentQuery } from './services/useProjectDocuments';
import { getChatHistory } from './services/useChat';

function App() {
  // Global application state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSources, setCurrentSources] = useState<Source[]>([]);
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  console.log("messages:", messages);

      useEffect(() => {
      fetchProjects();
      }, []);

      useEffect(() => {
        if (selectedProject) {
        fetchProjectDocuments(selectedProject?.id || '');
        fetchChatHistory(selectedProject?.id || '');
        }
      }, [selectedProject]);


    const fetchProjects = async () => {
      const response = await getProjectsQuery();
      if (response) {
       setProjects(response);
      } else {
        console.error('Failed to fetch projects');
      }
    };

    const fetchProjectDocuments = async (projectId: string) => {
      try {
        const response = await getProjectDocumentsQuery(projectId);
        if (response) {
          setDocuments(response);
        } else {
          console.error('Failed to fetch project documents');
        }
      } catch (error) {
        console.error('Error fetching project documents:', error);
      } 
    }

    const fetchChatHistory = async (projectId: string) => {
      try {
        const response = await getChatHistory({ project_id: projectId });
        console.log("Chat history response:", response);
        
        if (response) {
          const allMessages = response.flatMap((conversation: { messages: any; }) => conversation.messages);
          setMessages(allMessages);
        } else {
          console.error('Failed to fetch chat history');
        }
      }
      catch (error) {
        console.error('Error fetching chat history:', error);
      }
    }
    console.log("App messages:", messages);
    
  // Handle project creation
  const handleProjectCreate = useCallback((name: string, description?: string) => {
    const newProject: Project = {
      id: `project-${Date.now()}`,
      name,
      description,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      file_count: 0
    };
    
    setProjects(prev => [...prev, newProject]);
    console.log('[App] Project created:', newProject);
  }, []);

  // Handle project selection
  const handleProjectSelect = useCallback((project: Project) => {
    setSelectedProject(project);
    // Filter messages for this project
    setMessages(prev => prev.filter(m => m.projectId === project.id));
    console.log('[App] Project selected:', project);
  }, []);

  // Handle project deletion
  const handleProjectDelete = useCallback((projectId: string) => {
    setProjects(prev => prev.filter(p => p.id !== projectId));
    setDocuments(prev => prev.filter(d => d.projectId !== projectId));
    setMessages(prev => prev.filter(m => m.projectId !== projectId));
    const response = DeleteProjects({project_id:projectId});
    if (selectedProject?.id === projectId) {
      setSelectedProject(null);
    }
    console.log('[App] Project deleted:', projectId);
  }, [selectedProject]);

  // Handle file upload
  const handleFileUpload = useCallback((files: File[], projectId: string) => {

    const newDocuments: Document[] = files.map(file => ({
      id: `doc-${Date.now()}-${Math.random()}`,
      projectId:projectId,
      filename: file.name,
      fileType: file.name.split('.').pop()?.toLowerCase() as Document['fileType'],
      uploadedAt: new Date().toISOString(),
      size: file.size,
      status: 'processing'
    }));

    const formData = new FormData();
    formData.append('file', files[0]); // Append the file
    formData.append('projectId', projectId); // Add other metadata
    formData.append('filename', files[0].name);
    formData.append('fileType', files[0].name.split('.').pop()?.toLowerCase() || 'unknown');
    formData.append('size', files[0].size.toString());
    formData.append('uploadedAt', new Date().toISOString());
    formData.append('status', 'processing');

    const response = uploadDocumentQuery({ projectId,formData});
    if (!response) {    
      console.error('Failed to upload documents');
      return;
    }
    setDocuments(prev => [...prev, ...newDocuments]);
    
    // Update project file count
    setProjects(prev => prev.map(p => 
      p.id === projectId 
        ? { ...p, file_count: p.file_count + files.length, updatedAt: new Date().toISOString() }
        : p
    ));

    // Simulate processing (in production, this would be an API call)
    setTimeout(() => {
      setDocuments(prev => prev.map(doc => 
        newDocuments.find(d => d.id === doc.id)
          ? { ...doc, status: 'ready' as const }
          : doc
      ));
    }, 2000);
  }, []);

  // Handle sending a message
  const handleSendMessage = useCallback(async (content: string) => {
    if (!selectedProject) return;
   setIsLoading(true);
    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      projectId: selectedProject.id,
      content,
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
  }, [selectedProject]);

  // Handle source click
  const handleSourceClick = useCallback((sources: Source[]) => {
    setCurrentSources(sources);
    setIsSourcePanelOpen(true);
  }, []);

  const handleToggleDarkMode = () => setDarkMode((prev) => !prev);

  return (
    <div className={darkMode ? 'bg-gray-900 text-white min-h-screen' : 'bg-white text-gray-900 min-h-screen'}>
      <div className="flex h-screen">
        {/* Left Panel - Projects */}
        <ProjectPanel
          projects={projects}
          selectedProject={selectedProject}
          documents={documents}
          onProjectSelect={handleProjectSelect}
          onProjectCreate={handleProjectCreate}
          onProjectDelete={handleProjectDelete}
          onFileUpload={handleFileUpload}
          fetchProjects={fetchProjects}
          darkMode={darkMode}
        />

        {/* Middle Panel - Chat */}
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          selectedProjectName={selectedProject?.name}
          selectedProjectId={selectedProject?.id || ''}
          onSendMessage={handleSendMessage}
          onSourceClick={handleSourceClick}
          setMessages={setMessages}
          setIsLoading={setIsLoading}
          darkMode={darkMode}
          onToggleDarkMode={handleToggleDarkMode}
        />

        {/* Right Panel - Sources (conditional) */}
        <SourcePanel
          sources={currentSources}
          isOpen={isSourcePanelOpen}
          onClose={() => setIsSourcePanelOpen(false)}
          darkMode={darkMode}
        />
      </div>
    </div>
  );
}

export default App;