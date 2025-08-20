// File: frontend/src/App.tsx
// Purpose: Main application component that orchestrates all panels

import React, { useState, useCallback } from 'react';
import './App.css';
import ProjectPanel from './components/ProjectPanel/ProjectPanel';
import ChatPanel from './components/ChatPanel/ChatPanel';
import SourcePanel from './components/SourcePanel/SourcePanel';
import { Project, Document, ChatMessage, Source } from './types';

function App() {
  // Global application state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSources, setCurrentSources] = useState<Source[]>([]);
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Handle project creation
  const handleProjectCreate = useCallback((name: string, description?: string) => {
    const newProject: Project = {
      id: `project-${Date.now()}`,
      name,
      description,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      fileCount: 0
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
    
    if (selectedProject?.id === projectId) {
      setSelectedProject(null);
    }
    console.log('[App] Project deleted:', projectId);
  }, [selectedProject]);

  // Handle file upload
  const handleFileUpload = useCallback((files: File[], projectId: string) => {
    console.log('[App] Uploading files:', files.map(f => f.name));
    
    // Create document records
    const newDocuments: Document[] = files.map(file => ({
      id: `doc-${Date.now()}-${Math.random()}`,
      projectId,
      filename: file.name,
      fileType: file.name.split('.').pop()?.toLowerCase() as Document['fileType'],
      uploadedAt: new Date().toISOString(),
      size: file.size,
      status: 'processing'
    }));

    setDocuments(prev => [...prev, ...newDocuments]);
    
    // Update project file count
    setProjects(prev => prev.map(p => 
      p.id === projectId 
        ? { ...p, fileCount: p.fileCount + files.length, updatedAt: new Date().toISOString() }
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

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      projectId: selectedProject.id,
      content,
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate API call (in production, this would call your FastAPI backend)
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        projectId: selectedProject.id,
        content: `This is a simulated response for: "${content}"\n\nIn production, this will:\n1. Send your query to the FastAPI backend\n2. Search through documents using Pinecone vector database\n3. Generate an answer using OpenAI GPT-4\n4. Return relevant source chunks`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        sources: [
          {
            documentId: 'doc-1',
            documentName: 'Example Document.pdf',
            chunk: 'This is a relevant excerpt from your document that answers the question. In production, this will be actual content from your uploaded files.',
            pageNumber: 5,
            relevanceScore: 0.92
          }
        ]
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  }, [selectedProject]);

  // Handle source click
  const handleSourceClick = useCallback((sources: Source[]) => {
    setCurrentSources(sources);
    setIsSourcePanelOpen(true);
  }, []);

  return (
    <div className="flex h-screen bg-gray-100 font-poppins">
      {/* Left Panel - Projects */}
      <ProjectPanel
        projects={projects}
        selectedProject={selectedProject}
        documents={documents}
        onProjectSelect={handleProjectSelect}
        onProjectCreate={handleProjectCreate}
        onProjectDelete={handleProjectDelete}
        onFileUpload={handleFileUpload}
      />

      {/* Middle Panel - Chat */}
      <ChatPanel
        messages={messages?.filter(m => m.projectId === selectedProject?.id)}
        isLoading={isLoading}
        selectedProjectName={selectedProject?.name}
        onSendMessage={handleSendMessage}
        onSourceClick={handleSourceClick}
        setMessages={setMessages}
      />

      {/* Right Panel - Sources (conditional) */}
      <SourcePanel
        sources={currentSources}
        isOpen={isSourcePanelOpen}
        onClose={() => setIsSourcePanelOpen(false)}
      />
    </div>
  );
}

export default App;