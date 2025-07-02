"""
Vector Database for OllamaX-AI Memory System
"""

import asyncio
import json
import os
import pickle
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: Optional[float] = None

class VectorDB:
    """
    Local vector database for storing and retrieving contextual information
    Uses simple similarity search with optional ChromaDB integration
    """
    
    def __init__(self, db_path: str = "./memory/vector_store", use_chromadb: bool = True):
        self.db_path = db_path
        self.use_chromadb = use_chromadb
        self.documents = {}
        self.embeddings = {}
        self.chroma_client = None
        self.collection = None
        
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
        
    async def initialize(self):
        """Initialize the vector database"""
        try:
            if self.use_chromadb:
                await self._initialize_chromadb()
            else:
                await self._initialize_simple_db()
            
            logger.info("Vector database initialized successfully")
            
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed, falling back to simple DB: {e}")
            self.use_chromadb = False
            await self._initialize_simple_db()
    
    async def _initialize_chromadb(self):
        """Initialize ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.chroma_client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection("ollamax_memory")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="ollamax_memory",
                    metadata={"description": "OllamaX-AI memory storage"}
                )
                
        except ImportError:
            raise Exception("ChromaDB not available, install with: pip install chromadb")
    
    async def _initialize_simple_db(self):
        """Initialize simple file-based database"""
        self.documents_file = os.path.join(self.db_path, "documents.pkl")
        self.embeddings_file = os.path.join(self.db_path, "embeddings.pkl")
        
        # Load existing data
        if os.path.exists(self.documents_file):
            try:
                with open(self.documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load documents: {e}")
                self.documents = {}
        
        if os.path.exists(self.embeddings_file):
            try:
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load embeddings: {e}")
                self.embeddings = {}
    
    async def store(self, document: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """Store a document in the vector database"""
        
        if doc_id is None:
            doc_id = self._generate_doc_id()
        
        content = document.get('content', str(document))
        metadata = document.get('metadata', {})
        
        # Generate embedding
        embedding = await self._generate_embedding(content)
        
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata,
            embedding=embedding,
            timestamp=asyncio.get_event_loop().time()
        )
        
        if self.use_chromadb and self.collection:
            try:
                # Store in ChromaDB
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id],
                    embeddings=[embedding] if embedding else None
                )
            except Exception as e:
                logger.error(f"ChromaDB storage failed: {e}")
                # Fallback to simple storage
                await self._store_simple(doc)
        else:
            await self._store_simple(doc)
        
        return doc_id
    
    async def _store_simple(self, document: Document):
        """Store document in simple file-based database"""
        self.documents[document.id] = document
        if document.embedding:
            self.embeddings[document.id] = document.embedding
        
        # Persist to disk
        try:
            with open(self.documents_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            if self.embeddings:
                with open(self.embeddings_file, 'wb') as f:
                    pickle.dump(self.embeddings, f)
                    
        except Exception as e:
            logger.error(f"Failed to persist documents: {e}")
    
    async def search(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        
        if self.use_chromadb and self.collection:
            try:
                return await self._search_chromadb(query, limit)
            except Exception as e:
                logger.error(f"ChromaDB search failed: {e}")
                return await self._search_simple(query, limit, threshold)
        else:
            return await self._search_simple(query, limit, threshold)
    
    async def _search_chromadb(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using ChromaDB"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    'id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0.0,
                    'similarity': 1.0 - (results['distances'][0][i] if results['distances'] else 0.0)
                })
        
        return documents
    
    async def _search_simple(self, query: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Search using simple similarity calculation"""
        
        if not self.documents:
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        if not query_embedding:
            # Fallback to text matching
            return await self._search_text_match(query, limit)
        
        # Calculate similarities
        similarities = []
        for doc_id, doc in self.documents.items():
            if doc.embedding:
                similarity = self._calculate_similarity(query_embedding, doc.embedding)
                if similarity >= threshold:
                    similarities.append((doc_id, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, similarity in similarities[:limit]:
            doc = self.documents[doc_id]
            results.append({
                'id': doc_id,
                'content': doc.content,
                'metadata': doc.metadata,
                'similarity': similarity,
                'timestamp': doc.timestamp
            })
        
        return results
    
    async def _search_text_match(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback text matching search"""
        
        query_words = set(query.lower().split())
        matches = []
        
        for doc_id, doc in self.documents.items():
            doc_words = set(doc.content.lower().split())
            overlap = len(query_words.intersection(doc_words))
            
            if overlap > 0:
                score = overlap / len(query_words.union(doc_words))
                matches.append((doc_id, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in matches[:limit]:
            doc = self.documents[doc_id]
            results.append({
                'id': doc_id,
                'content': doc.content,
                'metadata': doc.metadata,
                'similarity': score,
                'timestamp': doc.timestamp
            })
        
        return results
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        
        if self.use_chromadb and self.collection:
            try:
                results = self.collection.get(ids=[doc_id])
                if results['documents']:
                    return {
                        'id': doc_id,
                        'content': results['documents'][0],
                        'metadata': results['metadatas'][0] if results['metadatas'] else {}
                    }
            except Exception as e:
                logger.error(f"ChromaDB get failed: {e}")
        
        # Fallback to simple storage
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            return {
                'id': doc_id,
                'content': doc.content,
                'metadata': doc.metadata,
                'timestamp': doc.timestamp
            }
        
        return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        
        if self.use_chromadb and self.collection:
            try:
                self.collection.delete(ids=[doc_id])
            except Exception as e:
                logger.error(f"ChromaDB delete failed: {e}")
        
        # Remove from simple storage
        if doc_id in self.documents:
            del self.documents[doc_id]
            if doc_id in self.embeddings:
                del self.embeddings[doc_id]
            
            # Persist changes
            await self._store_simple(Document("", "", {}))  # Trigger persistence
            return True
        
        return False
    
    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all documents"""
        
        documents = []
        doc_items = list(self.documents.items())[offset:offset + limit]
        
        for doc_id, doc in doc_items:
            documents.append({
                'id': doc_id,
                'content': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                'metadata': doc.metadata,
                'timestamp': doc.timestamp
            })
        
        return documents
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        return {
            'total_documents': len(self.documents),
            'total_embeddings': len(self.embeddings),
            'database_type': 'chromadb' if self.use_chromadb else 'simple',
            'storage_path': self.db_path
        }
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        
        try:
            # Try to use sentence transformers if available
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight model for embeddings
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text).tolist()
            return embedding
            
        except ImportError:
            # Fallback to simple hash-based embedding
            return self._simple_embedding(text)
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Generate simple hash-based embedding"""
        
        # Create a simple embedding based on character frequencies
        embedding = [0.0] * 384  # Match sentence transformer dimension
        
        for i, char in enumerate(text.lower()[:384]):
            embedding[i % 384] += ord(char) / 1000.0
        
        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        
        if len(embedding1) != len(embedding2):
            return 0.0
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _generate_doc_id(self) -> str:
        """Generate unique document ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def close(self):
        """Close the database connection"""
        if self.chroma_client:
            # ChromaDB doesn't need explicit closing
            pass
        
        # Ensure final persistence for simple DB
        if not self.use_chromadb and self.documents:
            try:
                with open(self.documents_file, 'wb') as f:
                    pickle.dump(self.documents, f)
                
                if self.embeddings:
                    with open(self.embeddings_file, 'wb') as f:
                        pickle.dump(self.embeddings, f)
            except Exception as e:
                logger.error(f"Failed to persist on close: {e}")
    
    # Utility methods for chunking and processing
    async def store_large_document(self, content: str, metadata: Dict[str, Any], chunk_size: int = 1000) -> List[str]:
        """Store large document by chunking it"""
        
        chunks = self._chunk_text(content, chunk_size)
        doc_ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'is_chunk': True,
                'parent_document': metadata.get('id', 'unknown')
            })
            
            doc_id = await self.store({
                'content': chunk,
                'metadata': chunk_metadata
            })
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Chunk text into smaller pieces"""
        
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def store_codebase(self, codebase_path: str) -> List[str]:
        """Store entire codebase for context"""
        
        doc_ids = []
        
        for root, dirs, files in os.walk(codebase_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
            
            for file in files:
                if self._is_code_file(file):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        metadata = {
                            'type': 'code_file',
                            'file_path': file_path,
                            'file_name': file,
                            'file_extension': os.path.splitext(file)[1],
                            'relative_path': os.path.relpath(file_path, codebase_path)
                        }
                        
                        # Store large files in chunks
                        if len(content) > 2000:
                            chunk_ids = await self.store_large_document(content, metadata, 1500)
                            doc_ids.extend(chunk_ids)
                        else:
                            doc_id = await self.store({
                                'content': content,
                                'metadata': metadata
                            })
                            doc_ids.append(doc_id)
                            
                    except Exception as e:
                        logger.warning(f"Failed to store file {file_path}: {e}")
        
        return doc_ids
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
            '.html', '.css', '.scss', '.less', '.xml', '.json',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.txt', '.rst', '.sql', '.sh', '.bash', '.zsh'
        }
        
        return os.path.splitext(filename)[1].lower() in code_extensions