// File: frontend/src/types/index.ts
// Purpose: Central type definitions for the entire application
// These types ensure type safety across all components

// Project type - represents a document collection/folder
export interface Project {
  id: string;                    // Unique identifier for the project
  name: string;                   // Display name of the project
  description?: string;           // Optional description (? means optional)
  createdAt: string;             // ISO timestamp when created
  updatedAt: string;             // ISO timestamp when last modified
  fileCount: number;             // Number of files in this project
}

// Document/File type - represents an uploaded file
export interface Document {
  id: string;                    // Unique identifier for the document
  projectId: string;             // Links document to its parent project
  filename: string;              // Original filename
  fileType: 'pdf' | 'docx' | 'xlsx' | 'doc' | 'xls';  // Allowed file types
  uploadedAt: string;            // ISO timestamp when uploaded
  size: number;                  // File size in bytes
  status: 'processing' | 'ready' | 'error';  // Current processing status
}

// Chat message type - represents a single message in the conversation
export interface ChatMessage {
  id: string;                    // Unique identifier for the message
  projectId: string;             // Links message to its project context
  content: string;               // The actual message text
  role: 'user' | 'assistant';   // Who sent the message
  timestamp: string;             // ISO timestamp when sent
  sources?: Source[];            // Optional array of source references
}

// Source reference type - represents a document chunk used in an answer
export interface Source {
  documentId: string;            // Which document this chunk came from
  documentName: string;          // Human-readable document name
  chunk: string;                 // The actual text excerpt
  pageNumber?: number;           // Optional page number
  relevanceScore?: number;       // Optional similarity score (0-1)
}

// API Response wrapper - standardizes backend responses
export interface ApiResponse<T> {
  data: T;                       // The actual response data
  message?: string;              // Optional success/info message
  error?: string;                // Optional error message
}

// File upload response - what backend returns after upload
export interface FileUploadResponse {
  documentId: string;            // ID of the uploaded document
  status: 'success' | 'error';  // Upload status
  message?: string;              // Optional status message
}

// Query request - what we send to backend for RAG queries
export interface QueryRequest {
  projectId: string;             // Which project to search in
  query: string;                 // The user's question
  maxResults?: number;           // Optional limit on sources returned
}

// Debug helper: Log type information
console.log('[Types] Type definitions loaded successfully');