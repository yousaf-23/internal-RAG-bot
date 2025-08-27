"""
Chat Service with RAG Integration
==================================
Purpose: Handle chat interactions using RAG (Retrieval-Augmented Generation)
Author: RAG System Development
Date: 2024

This module handles:
1. Processing user questions
2. Retrieving relevant context from Pinecone
3. Generating responses using GPT-4
4. Managing conversation history
5. Providing source citations

Architecture Flow:
User Question → Embedding → Pinecone Search → Context Retrieval → GPT-4 → Response
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time

# OpenAI for chat completion
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    print("[ChatService] ✅ OpenAI SDK available")
except ImportError:
    OPENAI_AVAILABLE = False
    print("[ChatService] ❌ OpenAI SDK not available - install openai")

# Import our services
from app.config import settings
from app.embeddings_service import EmbeddingsService
from app.pinecone_service import PineconeService
from app.database import get_db, Message, Project, Document

# ============================================================================
# CHAT SERVICE CLASS
# ============================================================================

class ChatService:
    """
    Service for handling chat interactions with RAG.
    
    This service:
    1. Takes user questions
    2. Searches for relevant document chunks
    3. Generates contextual responses
    4. Maintains conversation history
    """
    
    def __init__(self):
        """
        Initialize the chat service with necessary components.
        """
        print("\n[ChatService] Initializing...")
        
        # Check OpenAI availability
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai")
        
        # Check API key
        if not settings.openai_api_key:
            print("[ChatService] ⚠️  WARNING: OpenAI API key not set!")
            self.client = None
        else:
            try:
                # Initialize OpenAI client
                self.client = OpenAI(api_key=settings.openai_api_key)
                print("[ChatService] ✅ OpenAI client initialized")
            except Exception as e:
                print(f"[ChatService] ❌ Failed to initialize OpenAI: {e}")
                self.client = None
        
        # Initialize other services
        try:
            self.embeddings_service = EmbeddingsService()
            print("[ChatService] ✅ Embeddings service initialized")
        except Exception as e:
            print(f"[ChatService] ⚠️  Embeddings service failed: {e}")
            self.embeddings_service = None
        
        try:
            self.pinecone_service = PineconeService()
            print("[ChatService] ✅ Pinecone service initialized")
        except Exception as e:
            print(f"[ChatService] ⚠️  Pinecone service failed: {e}")
            self.pinecone_service = None
        
        # Configuration
        self.chat_model = settings.openai_model  # Default: gpt-4-turbo-preview
        self.max_context_chunks = 5  # Maximum chunks to include in context
        self.temperature = 0.2  # Creativity level (0-1)
        self.max_tokens = 2000  # Maximum response length
        
        print(f"[ChatService] Configuration:")
        print(f"  - Chat model: {self.chat_model}")
        print(f"  - Max context chunks: {self.max_context_chunks}")
        print(f"  - Temperature: {self.temperature}")
        print("[ChatService] ✅ Initialization complete\n")
    
    def search_relevant_context(
        self, 
        query: str, 
        project_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks based on the query.
        
        Args:
            query: The user's question
            project_id: Optional project ID to filter results
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with metadata
        """
        print(f"\n[ChatService] Searching for context...")
        print(f"  Query: {query[:100]}...")
        print(f"  Project filter: {project_id if project_id else 'None'}")
        
        # Check if services are available
        if not self.embeddings_service or not self.pinecone_service:
            print("[ChatService] ⚠️  Required services not available")
            return []
        
        try:
            # Step 1: Generate embedding for the query
            print("\n[ChatService] Generating query embedding...")
            query_embedding = self.embeddings_service.generate_embedding(query)
            
            if not query_embedding:
                print("[ChatService] ❌ Failed to generate query embedding")
                return []
            
            # Step 2: Search Pinecone for similar chunks
            print(f"[ChatService] Searching Pinecone for top {top_k} chunks...")
            
            # # Build filter if project_id is provided
            # filter_dict = None
            # if project_id:
            #     filter_dict = {'project_id': project_id}
            
            # Perform search
            search_results = self.pinecone_service.search(
                query_embedding=query_embedding,
                top_k=top_k,
                # filter=filter_dict,
                include_metadata=True,
                project_namespace=project_id 
            )
            
            print(f"[ChatService] ✅ Found {len(search_results)} relevant chunks")
            
            # Debug: Show relevance scores
            for i, result in enumerate(search_results[:3], 1):
                print(f"  Chunk {i}: Score={result['score']:.4f}, Doc={result.get('document_id', 'N/A')}")
            
            return search_results
            
        except Exception as e:
            print(f"[ChatService] ❌ Context search error: {e}")
            return []
    
    def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using GPT-4 with the provided context.
        
        Args:
            query: The user's question
            context_chunks: Relevant document chunks
            conversation_history: Previous messages in the conversation
            system_prompt: Optional custom system prompt
            
        Returns:
            Dictionary containing the response and metadata
        """
        print(f"\n[ChatService] Generating response...")
        print(f"  Query: {query[:100]}...")
        print(f"  Context chunks: {len(context_chunks)}")
        print(f"  Conversation history: {len(conversation_history) if conversation_history else 0} messages")
        
        # Check if client is available
        if not self.client:
            print("[ChatService] ❌ OpenAI client not available")
            return {
                'success': False,
                'error': 'OpenAI client not initialized',
                'response': 'I apologize, but I cannot generate a response at this time. Please check the API configuration.'
            }
        
        try:
            # Step 1: Build the context from chunks
            context_text = self._build_context(context_chunks)
            
            # Step 2: Build the full prompt (system and user) using a single function
            messages = self._build_prompt(
                query=query,
                context=context_text,
                context_chunks=context_chunks,
                conversation_history=conversation_history
            )
            
            # Debug: Show token estimate
            estimated_tokens = sum(len(msg["content"]) / 4 for msg in messages)
            print(f"[ChatService] Estimated input tokens: {estimated_tokens:.0f}")
            
            # Step 3: Call GPT-4
            print("[ChatService] Calling GPT-4...")
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract the response
            assistant_message = response.choices[0].message.content
            
            # Extract token usage
            usage = response.usage
            total_tokens = usage.total_tokens if usage else estimated_tokens
            
            # Calculate cost (GPT-4 pricing as of 2024)
            # Input: $0.01 per 1K tokens, Output: $0.03 per 1K tokens
            input_cost = (usage.prompt_tokens / 1000) * 0.01 if usage else 0
            output_cost = (usage.completion_tokens / 1000) * 0.03 if usage else 0
            total_cost = input_cost + output_cost
            
            print(f"[ChatService] ✅ Response generated successfully")
            print(f"  Response time: {response_time:.2f} seconds")
            print(f"  Total tokens: {total_tokens}")
            print(f"  Estimated cost: ${total_cost:.4f}")
            
            return {
                'success': True,
                'response': assistant_message,
                'sources': self._extract_sources(context_chunks),
                'metadata': {
                    'model': self.chat_model,
                    'temperature': self.temperature,
                    'context_chunks_used': len(context_chunks),
                    'response_time': response_time,
                    'tokens_used': total_tokens,
                    'estimated_cost': total_cost
                }
            }
        except Exception as e:
            print(f"[ChatService] ❌ Response generation error: {e}")
            
            # Check for specific errors
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'response': 'I apologize, but I\'ve hit the API rate limit. Please wait a moment and try again.'
                }
            elif "context_length" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'Context too long',
                    'response': 'The context is too long for me to process. Please try a more specific question.'
                }
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'response': 'I apologize, but I encountered an error generating a response. Please try again.'
                }
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build a formatted context string from chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant context found in the documents."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '')
            doc_id = chunk.get('document_id', 'Unknown')
            score = chunk.get('score', 0)
            
            # Format each chunk with metadata
            context_part = f"[Source {i} - Document: {doc_id} - Relevance: {score:.2f}]\n{text}\n"
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> list:
        """
        Build the full prompt (system and user) for GPT-4.
        Returns a list of messages for OpenAI chat completion.
        """
        # Enhanced system prompt for in-depth, RAG-powered answers
        system_prompt = ("""
            You are an advanced Retrieval-Augmented Generation (RAG) assistant.
            You have access to a knowledge base of documents and your primary goal is to provide in-depth, comprehensive, and well-structured answers
            Always use the provided document context to support your responses, and synthesize information from multiple sources when possible.
            Sometimes you will only have access to partial document context. 
            When answering questions, if the context is incomplete, try to reason based on the available data and provide a structured response.
            If key parts of the information are missing, acknowledge the limitation and suggest what is required to complete the answer.
            Always focus on providing the most accurate response based on the context you have, and do not hesitate to clarify when something is unavailable.

            Guidelines:
            1. Analyze the user's question deeply and provide a thorough, multi-paragraph answer.
            2. Integrate and synthesize information from all relevant context chunks, not just the most relevant one.
            3. When possible, break down your answer into sections or steps, using headings, bullet points, or numbered lists for clarity.
            4. Clearly cite which document/source each key point comes from (e.g., [Source 1], [Source 2]).
            5. If the context is insufficient, explain what is missing and suggest what information would be needed.
            6. Maintain a professional, detailed, and helpful tone. Go beyond surface-level answers.
            7. If the user asks for a summary, provide a detailed summary. If they ask for an explanation, provide a step-by-step explanation.
            8. Never fabricate information. Only use what is present in the provided context.
            9. If multiple perspectives or conflicting information exist in the context, present them clearly.
            10. Use markdown formatting for clarity (e.g., **bold**, _italic_, lists, headings).
            11. Do not give any Hypothetical responses always make sure the response is comming from the entire data that is provided.
            12. If asked to perform a task, do the task yourself rather than tellings how to do th task.
            Remember: Your responses should be as in-depth and insightful as possible, leveraging all available context."""
        )

        # # User message with context
        # if context_chunks and any(chunk.get('score', 0) > 0.7 for chunk in context_chunks):
        #     relevance_note = "I found relevant information in your documents:"
        # else:
        #     relevance_note = "I found some potentially related information, though it may not directly answer your question:"

        user_message = (
            f"Context from documents:\n"
            # f"{relevance_note}\n\n"
            f"{context}\n\n"
            "---\n\n"
            f"User Question: {query}\n\n"
            "Please provide an in-depth, comprehensive answer based strictly on the context above. "
            "Synthesize information from all sources, cite them, and structure your answer for maximum clarity and depth. "
            "If the context is insufficient, explain what is missing."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        messages.append({"role": "user", "content": user_message})
        return messages
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract source information from chunks for citation.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of source information
        """
        sources = []
        seen_docs = set()
        
        for chunk in chunks:
            doc_id = chunk.get('document_id')
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append({
                    'document_id': doc_id,
                    'filename': chunk.get('metadata', {}).get('filename', 'Unknown'),
                    'chunk_index': chunk.get('chunk_index', 0),
                    'relevance_score': chunk.get('score', 0)
                })
        
        return sources
    
    def chat(
        self,
        project_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Main chat method that combines all RAG components.
        
        This is the primary method to use for chat interactions.
        
        Args:
            project_id: The project to search documents in
            query: The user's question
            conversation_id: Optional conversation ID for context
            save_to_db: Whether to save the interaction to database
            
        Returns:
            Complete response with answer, sources, and metadata
        """
        print(f"\n{'='*60}")
        print(f"[ChatService] Processing chat request")
        print(f"  Project: {project_id}")
        print(f"  Query: {query[:100]}...")
        print(f"{'='*60}")
        
        try:
            # Step 1: Search for relevant context
            print("\n[Step 1] Searching for relevant context...")
            context_chunks = self.search_relevant_context(
                query=query,
                project_id=project_id,
                top_k=self.max_context_chunks
            )
            
            if not context_chunks:
                print("[ChatService] ⚠️  No relevant context found")
                # Can still try to answer with general knowledge
            
            # Step 2: Get conversation history if conversation_id provided
            conversation_history = None
            if conversation_id and save_to_db:
                # TODO: Implement conversation history retrieval
                print(f"[Step 2] Loading conversation history: {conversation_id}")
                conversation_history = []
            
            # Step 3: Generate response
            print("\n[Step 3] Generating response with GPT-4...")
            response_data = self.generate_response(
                query=query,
                context_chunks=context_chunks,
                conversation_history=conversation_history
            )
            
            # Step 4: Save to database if requested
            if save_to_db and response_data['success']:
                print("\n[Step 4] Saving to database...")
                # TODO: Implement database saving
                # This would save both the user message and assistant response
            
            # Step 5: Format final response
            print("\n[Step 5] Formatting final response...")
            
            final_response = {
                'success': response_data['success'],
                'response': response_data.get('response', ''),
                'sources': response_data.get('sources', []),
                'metadata': {
                    'project_id': project_id,
                    'conversation_id': conversation_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'context_used': len(context_chunks) > 0,
                    'chunks_retrieved': len(context_chunks),
                    **response_data.get('metadata', {})
                }
            }
            
            print(f"\n{'='*60}")
            print("[ChatService] ✅ Chat request completed successfully")
            print(f"{'='*60}\n")
            
            return final_response
            
        except Exception as e:
            print(f"\n[ChatService] ❌ Chat error: {e}")
            
            return {
                'success': False,
                'response': 'I apologize, but I encountered an error processing your request. Please try again.',
                'error': str(e),
                'metadata': {
                    'project_id': project_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }

# ============================================================================
# UTILITY FUNCTIONS FOR TESTING
# ============================================================================

def test_chat_service():
    """
    Test the chat service with sample queries.
    """
    print("\n" + "="*70)
    print("🧪 TESTING CHAT SERVICE")
    print("="*70)
    
    # Initialize service
    try:
        print("\n[Test] Initializing chat service...")
        chat_service = ChatService()
        print("[Test] ✅ Service initialized successfully")
    except Exception as e:
        print(f"[Test] ❌ Failed to initialize service: {e}")
        return
    
    # Test queries
    test_queries = [
        "What are vector databases?",
        "How does semantic search work?",
        "What are the benefits of RAG systems?"
    ]
    
    # Use a dummy project ID for testing
    test_project_id = "test_project"
    
    print("\n[Test] Running test queries...")
    print("-" * 40)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test Query {i}] {query}")
        
        # Test the chat method
        response = chat_service.chat(
            project_id=test_project_id,
            query=query,
            save_to_db=False  # Don't save test queries
        )
        
        if response['success']:
            print(f"✅ Response generated successfully")
            print(f"Response preview: {response['response'][:200]}...")
            print(f"Sources found: {len(response.get('sources', []))}")
            print(f"Response time: {response['metadata'].get('response_time', 0):.2f}s")
        else:
            print(f"❌ Failed to generate response: {response.get('error')}")
    
    print("\n" + "="*70)
    print("✅ CHAT SERVICE TEST COMPLETE")
    print("="*70)

# Run test if executed directly
if __name__ == "__main__":
    test_chat_service()