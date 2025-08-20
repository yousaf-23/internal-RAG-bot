"""
Pinecone Vector Database Service
=================================
Purpose: Store and search document embeddings using Pinecone
Author: RAG System Development
Date: 2024

This module handles:
1. Pinecone index creation and management
2. Storing embeddings with metadata
3. Semantic search functionality
4. Index statistics and monitoring

Architecture:
- Each document chunk becomes a vector in Pinecone
- Vectors are indexed by document_id_chunk_index
- Metadata includes text, document info, and timestamps
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# Pinecone client
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
    print("[PineconeService] ✅ Pinecone SDK available")
except ImportError:
    PINECONE_AVAILABLE = False
    print("[PineconeService] ❌ Pinecone SDK not available - install pinecone-client")

# Import our configuration
from app.config import settings

# ============================================================================
# PINECONE SERVICE CLASS
# ============================================================================

class PineconeService:
    """
    Service for managing vector storage and search using Pinecone.
    
    Features:
    - Create and manage Pinecone indexes
    - Store embeddings with metadata
    - Perform semantic search
    - Monitor index usage and statistics
    """
    
    def __init__(self):
        """
        Initialize the Pinecone service and connect to the index.
        """
        print("\n[PineconeService] Initializing...")
        
        # Check if Pinecone is available
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone SDK not installed. Run: pip install pinecone-client")
        
        # Initialize attributes
        self.index = None
        self.index_name = settings.pinecone_index_name  # Default: "rag-documents"
        self.dimension = settings.embedding_dimension  # Default: 1536
        
        # Check API key
        if not settings.pinecone_api_key:
            print("[PineconeService] ⚠️  WARNING: Pinecone API key not set!")
            print("[PineconeService] Set PINECONE_API_KEY in your .env file")
            print("[PineconeService] Get your key from: https://app.pinecone.io/")
            self.pc = None
        else:
            # Initialize Pinecone client
            try:
                print("[PineconeService] Connecting to Pinecone...")
                print(f"[PineconeService] API Key: {settings.pinecone_api_key[:8]}...")
                
                # Initialize Pinecone with new client structure (as of 2024)
                self.pc = Pinecone(api_key=settings.pinecone_api_key)
                
                print(f"[PineconeService] ✅ Pinecone client initialized")
                
                # Connect to or create index
                self._setup_index()
                
            except Exception as e:
                print(f"[PineconeService] ❌ Failed to initialize Pinecone: {e}")
                self.pc = None
                self.index = None
        
        print("[PineconeService] ✅ Initialization complete\n")
    
    def _setup_index(self):
        """
        Set up the Pinecone index - create if doesn't exist, connect if it does.
        """
        try:
            print(f"[PineconeService] Setting up index: {self.index_name}")
            
            # List existing indexes
            existing_indexes = self.pc.list_indexes()
            print(f"[PineconeService] Existing indexes: {[idx.name for idx in existing_indexes]}")
            
            # Check if our index exists
            index_exists = any(idx.name == self.index_name for idx in existing_indexes)
            
            if not index_exists:
                print(f"[PineconeService] Index '{self.index_name}' doesn't exist. Creating...")
                
                # Create the index with serverless spec (recommended for free tier)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,  # 1536 for OpenAI embeddings
                    metric='cosine',  # Cosine similarity for semantic search
                    spec=ServerlessSpec(
                        cloud='aws',  # or 'gcp' based on your region
                        region='us-east-1'  # or your preferred region
                    )
                )
                
                print(f"[PineconeService] ✅ Index '{self.index_name}' created!")
                
                # Wait for index to be ready
                print("[PineconeService] Waiting for index to be ready...")
                time.sleep(10)  # Initial wait
                
                # Poll until ready
                max_attempts = 30
                for i in range(max_attempts):
                    try:
                        index_description = self.pc.describe_index(self.index_name)
                        if index_description.status.ready:
                            print("[PineconeService] ✅ Index is ready!")
                            break
                    except:
                        pass
                    
                    print(f"[PineconeService] Waiting... ({i+1}/{max_attempts})")
                    time.sleep(2)
            else:
                print(f"[PineconeService] ✅ Index '{self.index_name}' already exists")
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            
            # Get index statistics
            stats = self.index.describe_index_stats()
            print(f"[PineconeService] Index statistics:")
            print(f"  - Total vectors: {stats.total_vector_count}")
            print(f"  - Dimension: {stats.dimension}")
            print(f"  - Index fullness: {stats.index_fullness:.2%}")
            
        except Exception as e:
            print(f"[PineconeService] ❌ Error setting up index: {e}")
            print(f"[PineconeService] Debug info:")
            print(f"  - Index name: {self.index_name}")
            print(f"  - Dimension: {self.dimension}")
            raise
    
    def upsert_embeddings(
        self, 
        document_id: str, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ) -> Dict[str, Any]:
        """
        Store document chunks and their embeddings in Pinecone.
        
        Args:
            document_id: Unique identifier for the document
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors (same order as chunks)
            
        Returns:
            Dictionary with upload statistics
        """
        print(f"\n[PineconeService] Upserting embeddings for document: {document_id}")
        print(f"  - Number of chunks: {len(chunks)}")
        print(f"  - Number of embeddings: {len(embeddings)}")
        
        if not self.index:
            print("[PineconeService] ❌ Index not initialized!")
            return {'success': False, 'error': 'Index not initialized'}
        
        # Prepare vectors for upsert
        vectors = []
        successful = 0
        failed = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Skip if embedding is None (failed to generate)
            if embedding is None:
                print(f"[PineconeService] ⚠️  Skipping chunk {i} - no embedding")
                failed += 1
                continue
            
            # Create unique ID for this chunk
            chunk_id = f"{document_id}_chunk_{i}"
            
            # Prepare metadata (Pinecone has limits on metadata size)
            # Maximum metadata size is 10KB per vector
            chunk_text = chunk.get('text', '')
            
            # Truncate text if too long for metadata (keep under 5000 chars to be safe)
            if len(chunk_text) > 5000:
                chunk_text = chunk_text[:5000] + "..."
            
            metadata = {
                'document_id': document_id,
                'chunk_index': i,
                'text': chunk_text,  # Store the actual text for retrieval
                'char_count': chunk.get('char_count', 0),
                'word_count': chunk.get('word_count', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add to vectors list
            vectors.append({
                'id': chunk_id,
                'values': embedding,
                'metadata': metadata
            })
            
            successful += 1
            
            # Debug: Show progress for large documents
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(chunks)} chunks...")
        
        # Upsert vectors to Pinecone in batches
        if vectors:
            try:
                print(f"[PineconeService] Upserting {len(vectors)} vectors to Pinecone...")
                
                # Pinecone recommends batch sizes of 100 or less
                batch_size = 100
                total_upserted = 0
                
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    
                    # Upsert batch
                    response = self.index.upsert(vectors=batch)
                    
                    total_upserted += response.upserted_count
                    print(f"  Batch {i//batch_size + 1}: Upserted {response.upserted_count} vectors")
                
                print(f"[PineconeService] ✅ Successfully upserted {total_upserted} vectors!")
                
                # Wait a moment for indexing
                time.sleep(1)
                
                # Verify by checking stats
                stats = self.index.describe_index_stats()
                print(f"[PineconeService] Updated index statistics:")
                print(f"  - Total vectors: {stats.total_vector_count}")
                
                return {
                    'success': True,
                    'upserted': total_upserted,
                    'successful': successful,
                    'failed': failed,
                    'total_vectors_in_index': stats.total_vector_count
                }
                
            except Exception as e:
                print(f"[PineconeService] ❌ Error upserting vectors: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'successful': 0,
                    'failed': len(chunks)
                }
        else:
            print("[PineconeService] ⚠️  No valid vectors to upsert")
            return {
                'success': False,
                'error': 'No valid embeddings',
                'successful': 0,
                'failed': len(chunks)
            }
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filter: Optional[Dict] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Pinecone.
        
        Args:
            query_embedding: The query vector to search for
            top_k: Number of results to return
            filter: Optional metadata filter
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of search results with scores and metadata
        """
        print(f"\n[PineconeService] Searching for {top_k} similar vectors...")
        
        if not self.index:
            print("[PineconeService] ❌ Index not initialized!")
            return []
        
        try:
            # Perform the search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata
            )
            
            # Process results
            search_results = []
            for match in results.matches:
                result = {
                    'id': match.id,
                    'score': match.score,  # Cosine similarity (higher is better, max 1.0)
                    'document_id': match.metadata.get('document_id') if match.metadata else None,
                    'chunk_index': match.metadata.get('chunk_index') if match.metadata else None,
                    'text': match.metadata.get('text') if match.metadata else None,
                    'metadata': match.metadata if match.metadata else {}
                }
                search_results.append(result)
                
                # Debug: Show top results
                if len(search_results) <= 3:
                    preview = result['text'][:100] if result['text'] else 'No text'
                    print(f"  Result {len(search_results)}: Score={result['score']:.4f}")
                    print(f"    Preview: {preview}...")
            
            print(f"[PineconeService] ✅ Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            print(f"[PineconeService] ❌ Search error: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all vectors for a specific document.
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n[PineconeService] Deleting vectors for document: {document_id}")
        
        if not self.index:
            print("[PineconeService] ❌ Index not initialized!")
            return False
        
        try:
            # We need to find all chunk IDs for this document
            # Since we use the pattern: document_id_chunk_N
            # We can use metadata filtering to find them
            
            # First, query to find all chunks for this document
            # Note: Pinecone doesn't support wildcard deletes, so we need IDs
            
            # Get a sample vector to use for querying (any vector will do)
            stats = self.index.describe_index_stats()
            if stats.total_vector_count == 0:
                print("[PineconeService] No vectors in index")
                return True
            
            # Query with a dummy vector but filter by document_id
            dummy_vector = [0.0] * self.dimension
            results = self.index.query(
                vector=dummy_vector,
                top_k=1000,  # Get up to 1000 chunks
                filter={'document_id': document_id},
                include_metadata=False
            )
            
            # Extract chunk IDs
            chunk_ids = [match.id for match in results.matches]
            
            if chunk_ids:
                print(f"[PineconeService] Found {len(chunk_ids)} chunks to delete")
                
                # Delete the chunks
                self.index.delete(ids=chunk_ids)
                
                print(f"[PineconeService] ✅ Deleted {len(chunk_ids)} vectors")
                return True
            else:
                print(f"[PineconeService] No chunks found for document {document_id}")
                return True
                
        except Exception as e:
            print(f"[PineconeService] ❌ Delete error: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get current index statistics.
        
        Returns:
            Dictionary with index statistics
        """
        if not self.index:
            return {'error': 'Index not initialized'}
        
        try:
            stats = self.index.describe_index_stats()
            
            return {
                'index_name': self.index_name,
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': stats.namespaces
            }
        except Exception as e:
            return {'error': str(e)}

# ============================================================================
# UTILITY FUNCTIONS FOR TESTING
# ============================================================================

def test_pinecone_service():
    """
    Test the Pinecone service with sample data.
    """
    print("\n" + "="*70)
    print("🧪 TESTING PINECONE SERVICE")
    print("="*70)
    
    # Initialize service
    try:
        print("\n[Test] Initializing Pinecone service...")
        service = PineconeService()
        print("[Test] ✅ Service initialized successfully")
    except Exception as e:
        print(f"[Test] ❌ Failed to initialize service: {e}")
        print("\n[Test] Debugging steps:")
        print("1. Check if Pinecone is installed: pip install pinecone-client")
        print("2. Check your .env file has PINECONE_API_KEY set")
        print("3. Verify you have a Pinecone account at https://app.pinecone.io/")
        return
    
    # Test 1: Check index statistics
    print("\n[Test 1] Index Statistics")
    print("-" * 40)
    
    stats = service.get_index_stats()
    print(f"Index stats:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # Test 2: Create and store test embeddings
    print("\n[Test 2] Storing Test Embeddings")
    print("-" * 40)
    
    # Create test data
    test_document_id = f"test_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    test_chunks = [
        {
            'text': 'Machine learning is a subset of artificial intelligence.',
            'char_count': 56,
            'word_count': 8
        },
        {
            'text': 'Python is a popular programming language for data science.',
            'char_count': 58,
            'word_count': 9
        },
        {
            'text': 'Neural networks are inspired by the human brain.',
            'char_count': 49,
            'word_count': 8
        }
    ]
    
    # Generate simple test embeddings (normally these come from OpenAI)
    import random
    random.seed(42)  # For reproducibility
    test_embeddings = [
        [random.random() * 2 - 1 for _ in range(service.dimension)]
        for _ in test_chunks
    ]
    
    print(f"Storing {len(test_chunks)} test chunks...")
    result = service.upsert_embeddings(test_document_id, test_chunks, test_embeddings)
    
    if result['success']:
        print(f"✅ Successfully stored embeddings!")
        print(f"  - Upserted: {result['upserted']}")
        print(f"  - Total vectors in index: {result['total_vectors_in_index']}")
    else:
        print(f"❌ Failed to store embeddings: {result.get('error')}")
    
    # Test 3: Search for similar vectors
    print("\n[Test 3] Semantic Search")
    print("-" * 40)
    
    # Create a query embedding (normally from OpenAI)
    query_embedding = [random.random() * 2 - 1 for _ in range(service.dimension)]
    
    print("Searching for similar vectors...")
    search_results = service.search(query_embedding, top_k=3)
    
    if search_results:
        print(f"✅ Found {len(search_results)} results:")
        for i, result in enumerate(search_results, 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result['score']:.4f}")
            print(f"    Text: {result['text'][:100] if result['text'] else 'N/A'}...")
    else:
        print("No results found")
    
    # Test 4: Clean up test data
    print("\n[Test 4] Cleanup")
    print("-" * 40)
    
    if service.delete_document(test_document_id):
        print(f"✅ Deleted test document vectors")
    else:
        print(f"⚠️  Could not delete test vectors")
    
    print("\n" + "="*70)
    print("✅ PINECONE SERVICE TEST COMPLETE")
    print("="*70)

# Run test if executed directly
if __name__ == "__main__":
    test_pinecone_service()