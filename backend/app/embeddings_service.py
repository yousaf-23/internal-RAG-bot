"""
OpenAI Embeddings Service - FIXED VERSION
==========================================
Purpose: Generate embeddings for text chunks using OpenAI's API
Author: RAG System Development
Date: 2024

This module handles:
1. Generating embeddings for text chunks
2. Batch processing for efficiency
3. Error handling and retries
4. Cost tracking and optimization

FIXED: Attribute initialization order to prevent 'embedding_model' not found error
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# OpenAI SDK
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    print("[EmbeddingsService] ✅ OpenAI SDK available")
except ImportError:
    OPENAI_AVAILABLE = False
    print("[EmbeddingsService] ❌ OpenAI SDK not available - install openai")

# Import our configuration
from app.config import settings

# ============================================================================
# EMBEDDINGS SERVICE CLASS - FIXED VERSION
# ============================================================================

class EmbeddingsService:
    """
    Service for generating embeddings using OpenAI's API.
    
    Features:
    - Generate embeddings for single or multiple texts
    - Automatic retry on failure
    - Cost tracking
    - Progress reporting
    
    FIXED: Proper initialization order to prevent attribute errors
    """
    
    def __init__(self):
        """
        Initialize the embeddings service with OpenAI client.
        FIXED: Set all attributes BEFORE calling any methods that use them
        """
        print("\n[EmbeddingsService] Initializing...")
        
        # STEP 1: Initialize ALL attributes FIRST (before any method calls)
        # This prevents "attribute not found" errors
        
        # Configuration attributes - SET THESE FIRST!
        self.embedding_model = settings.embedding_model  # Default: text-embedding-3-small
        self.embedding_dimension = settings.embedding_dimension  # Default: 1536
        
        # Cost tracking attributes
        self.cost_per_1k_tokens = 0.00002  # $0.020 per 1M tokens for text-embedding-3-small
        self.total_tokens_used = 0
        self.total_api_calls = 0
        
        # Client attribute (will be set below)
        self.client = None
        
        print(f"[EmbeddingsService] Configuration loaded:")
        print(f"  - Model: {self.embedding_model}")
        print(f"  - Dimension: {self.embedding_dimension}")
        print(f"  - Cost: ${self.cost_per_1k_tokens:.5f} per 1K tokens")
        
        # STEP 2: Check if OpenAI SDK is available
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not installed. Run: pip install openai")
        
        # STEP 3: Check and validate API key
        if not settings.openai_api_key:
            print("[EmbeddingsService] ⚠️  WARNING: OpenAI API key not set!")
            print("[EmbeddingsService] Set OPENAI_API_KEY in your .env file")
            print("[EmbeddingsService] Get your key from: https://platform.openai.com/api-keys")
            # Leave client as None - methods will check for this
        else:
            # STEP 4: Initialize OpenAI client (AFTER all attributes are set)
            try:
                print("[EmbeddingsService] Initializing OpenAI client...")
                self.client = OpenAI(api_key=settings.openai_api_key)
                print(f"[EmbeddingsService] ✅ OpenAI client initialized")
                
                # STEP 5: Test the API key (now all attributes are available)
                if self._test_api_key():
                    print("[EmbeddingsService] ✅ API connection verified")
                else:
                    print("[EmbeddingsService] ⚠️  API test failed, but continuing...")
                    
            except Exception as e:
                print(f"[EmbeddingsService] ❌ Failed to initialize OpenAI client: {e}")
                self.client = None
        
        print("[EmbeddingsService] ✅ Initialization complete\n")
    
    def _test_api_key(self):
        """
        Test if the OpenAI API key is valid by making a minimal request.
        FIXED: Now safely uses self.embedding_model which is guaranteed to exist
        """
        try:
            # Debug: Show what we're testing with
            print(f"[EmbeddingsService] Testing API key with model: {self.embedding_model}")
            
            # Make a test embedding request with minimal text
            response = self.client.embeddings.create(
                model=self.embedding_model,  # Now this attribute definitely exists
                input="test",
                encoding_format="float"
            )
            
            # Verify the response
            if response and response.data and len(response.data) > 0:
                embedding_dim = len(response.data[0].embedding)
                print(f"[EmbeddingsService] ✅ API key is valid!")
                print(f"[EmbeddingsService] Test embedding dimension: {embedding_dim}")
                return True
            else:
                print("[EmbeddingsService] ⚠️  Unexpected response format")
                return False
                
        except Exception as e:
            error_msg = str(e)
            
            # Detailed error analysis
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                print("[EmbeddingsService] ❌ Invalid API key!")
                print("[EmbeddingsService] Please check your OpenAI API key in .env file")
            elif "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                print("[EmbeddingsService] ⚠️  API key valid but quota exceeded")
                print("[EmbeddingsService] Add credits at: https://platform.openai.com/billing")
            elif "model" in error_msg.lower():
                print(f"[EmbeddingsService] ❌ Model '{self.embedding_model}' not available")
                print("[EmbeddingsService] Try using 'text-embedding-ada-002' instead")
            else:
                print(f"[EmbeddingsService] ❌ API test failed: {e}")
            
            return False
    
    def generate_embedding(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: The text to embed
            retry_count: Number of retries on failure
            
        Returns:
            List of floats (embedding vector) or None if failed
        """
        # Debug: Show what we're embedding
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"\n[EmbeddingsService] Generating embedding for text:")
        print(f"  Preview: {preview}")
        print(f"  Length: {len(text)} characters")
        
        # Check if client is available
        if not self.client:
            print("[EmbeddingsService] ❌ OpenAI client not initialized!")
            print("[EmbeddingsService] Check your API key in .env file")
            return None
        
        # Clean the text (remove excess whitespace)
        text = " ".join(text.split())
        
        # Check if text is empty
        if not text or len(text.strip()) == 0:
            print("[EmbeddingsService] ⚠️  Empty text, skipping")
            return None
        
        # Try to generate embedding with retries
        for attempt in range(retry_count):
            try:
                # Make API call
                print(f"[EmbeddingsService] API call attempt {attempt + 1}/{retry_count}...")
                
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text,
                    encoding_format="float"
                )
                
                # Extract embedding
                embedding = response.data[0].embedding
                
                # Track usage
                self.total_api_calls += 1
                # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
                estimated_tokens = len(text) / 4
                self.total_tokens_used += estimated_tokens
                
                # Calculate cost
                cost = (estimated_tokens / 1000) * self.cost_per_1k_tokens
                
                print(f"[EmbeddingsService] ✅ Embedding generated successfully!")
                print(f"  - Vector dimension: {len(embedding)}")
                print(f"  - Estimated tokens: {estimated_tokens:.0f}")
                print(f"  - Estimated cost: ${cost:.6f}")
                
                return embedding
                
            except Exception as e:
                print(f"[EmbeddingsService] ❌ Attempt {attempt + 1} failed: {e}")
                
                # Check for specific errors
                error_msg = str(e)
                if "rate_limit" in error_msg.lower():
                    # Rate limit hit - wait before retry
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    print(f"[EmbeddingsService] Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif "context_length" in error_msg.lower():
                    # Text too long
                    print(f"[EmbeddingsService] Text too long for model!")
                    print(f"[EmbeddingsService] Max length is ~8000 tokens (32000 chars)")
                    # Try truncating the text
                    if len(text) > 30000:  # Roughly 7500 tokens
                        text = text[:30000]
                        print(f"[EmbeddingsService] Truncated text to {len(text)} characters")
                    else:
                        return None
                elif attempt < retry_count - 1:
                    # Generic error - wait and retry
                    time.sleep(1)
                else:
                    # Final attempt failed
                    print(f"[EmbeddingsService] All attempts failed!")
                    return None
        
        return None
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        OpenAI allows batching up to 2048 embedding inputs in a single request,
        but we use smaller batches for better error handling.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each API call
            
        Returns:
            List of embeddings (same order as input texts)
        """
        print(f"\n{'='*60}")
        print(f"[EmbeddingsService] Batch Embedding Generation")
        print(f"  Total texts: {len(texts)}")
        print(f"  Batch size: {batch_size}")
        print(f"  Estimated batches: {(len(texts) + batch_size - 1) // batch_size}")
        print(f"{'='*60}")
        
        # Check if client is available
        if not self.client:
            print("[EmbeddingsService] ❌ OpenAI client not initialized!")
            return [None] * len(texts)
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            print(f"\n[EmbeddingsService] Processing batch {batch_num}/{total_batches}")
            print(f"  Texts in batch: {len(batch_texts)}")
            
            # Clean texts in batch
            cleaned_batch = []
            for text in batch_texts:
                cleaned = " ".join(text.split())
                if cleaned and len(cleaned.strip()) > 0:
                    cleaned_batch.append(cleaned)
                else:
                    cleaned_batch.append("empty")  # Placeholder for empty texts
            
            try:
                # Make batch API call
                print(f"[EmbeddingsService] Making batch API call...")
                
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=cleaned_batch,
                    encoding_format="float"
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                
                # Track usage
                self.total_api_calls += 1
                estimated_tokens = sum(len(text) / 4 for text in cleaned_batch)
                self.total_tokens_used += estimated_tokens
                
                # Calculate cost
                cost = (estimated_tokens / 1000) * self.cost_per_1k_tokens
                
                print(f"[EmbeddingsService] ✅ Batch {batch_num} completed!")
                print(f"  - Embeddings generated: {len(batch_embeddings)}")
                print(f"  - Estimated tokens: {estimated_tokens:.0f}")
                print(f"  - Estimated cost: ${cost:.6f}")
                
                embeddings.extend(batch_embeddings)
                
                # Small delay to avoid rate limits
                if i + batch_size < len(texts):
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"[EmbeddingsService] ❌ Batch {batch_num} failed: {e}")
                
                # Fall back to individual processing for this batch
                print(f"[EmbeddingsService] Falling back to individual processing...")
                for text in batch_texts:
                    embedding = self.generate_embedding(text, retry_count=2)
                    embeddings.append(embedding)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"[EmbeddingsService] Batch Processing Complete!")
        print(f"  Total embeddings: {len(embeddings)}")
        print(f"  Successful: {sum(1 for e in embeddings if e is not None)}")
        print(f"  Failed: {sum(1 for e in embeddings if e is None)}")
        print(f"  Total API calls: {self.total_api_calls}")
        print(f"  Total tokens used: {self.total_tokens_used:.0f}")
        print(f"  Total estimated cost: ${(self.total_tokens_used / 1000) * self.cost_per_1k_tokens:.6f}")
        print(f"{'='*60}\n")
        
        return embeddings
    
# ============================================================================
# UTILITY FUNCTIONS FOR TESTING
# ============================================================================

    def estimate_cost(self, texts: List[str]) -> Dict[str, Any]:
        """
        Estimate the cost of generating embeddings for given texts.
        
        Args:
            texts: List of texts to estimate cost for
            
        Returns:
            Dictionary with cost breakdown
        """
        # Estimate tokens (1 token ≈ 4 characters)
        total_chars = sum(len(text) for text in texts)
        estimated_tokens = total_chars / 4
        
        # Calculate cost
        estimated_cost = (estimated_tokens / 1000) * self.cost_per_1k_tokens
        
        return {
            'text_count': len(texts),
            'total_characters': total_chars,
            'estimated_tokens': int(estimated_tokens),
            'estimated_cost_usd': round(estimated_cost, 6),
            'model': self.embedding_model,
            'price_per_1k_tokens': self.cost_per_1k_tokens
        }

def test_embeddings_service():
    """
    Test the embeddings service with sample texts.
    This function helps verify the service is working correctly.
    """
    print("\n" + "="*70)
    print("🧪 TESTING EMBEDDINGS SERVICE")
    print("="*70)
    
    # Initialize service
    try:
        print("\n[Test] Initializing embeddings service...")
        service = EmbeddingsService()
        print("[Test] ✅ Service initialized successfully")
    except Exception as e:
        print(f"[Test] ❌ Failed to initialize service: {e}")
        print("\n[Test] Debugging steps:")
        print("1. Check if OpenAI is installed: pip install openai")
        print("2. Check your .env file has OPENAI_API_KEY set")
        print("3. Verify the API key starts with 'sk-'")
        return
    
    # Test texts
    test_texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language for data science.",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    # Test 1: Single embedding
    print("\n[Test 1] Single Embedding Generation")
    print("-" * 40)
    
    embedding = service.generate_embedding(test_texts[0])
    
    if embedding:
        print(f"✅ Embedding generated!")
        print(f"  - Dimension: {len(embedding)}")
        print(f"  - First 5 values: {embedding[:5]}")
        print(f"  - All values between -1 and 1: {all(-1 <= v <= 1 for v in embedding)}")
    else:
        print("❌ Failed to generate embedding")
        print("Debugging: Check the console output above for error details")
    
    # Test 2: Batch embeddings
    print("\n[Test 2] Batch Embedding Generation")
    print("-" * 40)
    
    embeddings = service.generate_embeddings_batch(test_texts, batch_size=2)
    
    if embeddings:
        print(f"✅ Batch processing complete!")
        print(f"  - Total embeddings: {len(embeddings)}")
        print(f"  - Successful: {sum(1 for e in embeddings if e is not None)}")
        
        # Check similarity (embeddings of similar texts should be more similar)
        if len(embeddings) >= 2 and embeddings[0] and embeddings[1]:
            # Calculate cosine similarity between first two embeddings
            import math
            
            def cosine_similarity(v1, v2):
                dot_product = sum(a * b for a, b in zip(v1, v2))
                magnitude1 = math.sqrt(sum(a * a for a in v1))
                magnitude2 = math.sqrt(sum(b * b for b in v2))
                return dot_product / (magnitude1 * magnitude2)
            
            similarity = cosine_similarity(embeddings[0], embeddings[1])
            print(f"  - Similarity between first two texts: {similarity:.4f}")
            print(f"    (Values closer to 1 = more similar)")
    
    # Test 3: Cost estimation
    print("\n[Test 3] Cost Estimation")
    print("-" * 40)
    
    cost_estimate = service.estimate_cost(test_texts)
    print(f"Cost estimate for {cost_estimate['text_count']} texts:")
    print(f"  - Total characters: {cost_estimate['total_characters']}")
    print(f"  - Estimated tokens: {cost_estimate['estimated_tokens']}")
    print(f"  - Estimated cost: ${cost_estimate['estimated_cost_usd']:.6f}")
    print(f"  - Model: {cost_estimate['model']}")
    
    print("\n" + "="*70)
    print("✅ EMBEDDINGS SERVICE TEST COMPLETE")
    print("="*70)

# Run test if executed directly
if __name__ == "__main__":
    test_embeddings_service()