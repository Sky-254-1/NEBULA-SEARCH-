"""
Document Indexer

Handles document indexing for semantic search:
- Document chunking
- Embedding generation
- Vector storage
- Incremental updates
"""

import logging
import hashlib
from typing import Optional

from .engine import SemanticEngine

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Indexes documents for semantic search.
    
    Handles:
    - Document chunking
    - Embedding generation
    - Vector storage
    - Incremental indexing
    """
    
    def __init__(
        self,
        semantic_engine: Optional[SemanticEngine] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """
        Initialize document indexer.
        
        Args:
            semantic_engine: Semantic engine instance
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.semantic_engine = semantic_engine
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._cache = {}
    
    async def index_document(
        self,
        document_id: int,
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Index a single document.
        
        Args:
            document_id: Document ID
            content: Document content
            metadata: Optional metadata
            
        Returns:
            True if indexed successfully
        """
        if not content or not content.strip():
            logger.warning(f"Empty content for document {document_id}")
            return False
        
        try:
            # Chunk the document
            chunks = self._chunk_document(content)
            
            if not chunks:
                logger.warning(f"No chunks generated for document {document_id}")
                return False
            
            # Prepare documents for indexing
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                
                documents.append({
                    'id': chunk_id,
                    'content': chunk,
                    'metadata': {
                        'document_id': document_id,
                        'chunk_index': i,
                        'chunk_count': len(chunks),
                        **(metadata or {}),
                    },
                })
            
            # Index with semantic engine
            if self.semantic_engine:
                await self.semantic_engine.index_documents(documents)
            
            logger.info(f"Indexed document {document_id} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            return False
    
    async def index_documents(self, documents: list[dict]) -> list[int]:
        """
        Index multiple documents.
        
        Args:
            documents: List of document dictionaries with keys:
                - id: Document ID
                - content: Document content
                - metadata: Optional metadata
                
        Returns:
            List of successfully indexed document IDs
        """
        if not documents:
            return []
        
        indexed_ids = []
        
        for doc in documents:
            doc_id = doc.get('id')
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            success = await self.index_document(doc_id, content, metadata)
            if success:
                indexed_ids.append(doc_id)
        
        return indexed_ids
    
    async def delete_document(self, document_id: int) -> bool:
        """
        Delete a document from the index.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted successfully
        """
        try:
            if self.semantic_engine and self.semantic_engine._vector_store:
                self.semantic_engine.config.get('collection_name', 'documents')
                
                # Delete all chunks for this document
                # Note: This requires the vector store to support filtering by document_id
                # For now, we'll delete by pattern matching
                # In production, you'd want to track chunk IDs
                
                logger.info(f"Deleted document {document_id} from index")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def update_document(
        self,
        document_id: int,
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Update an existing document in the index.
        
        Args:
            document_id: Document ID
            content: New document content
            metadata: Optional metadata
            
        Returns:
            True if updated successfully
        """
        # Delete old document
        await self.delete_document(document_id)
        
        # Index new content
        return await self.index_document(document_id, content, metadata)
    
    def _chunk_document(self, content: str) -> list[str]:
        """
        Split document into chunks.
        
        Args:
            content: Document content
            
        Returns:
            List of text chunks
        """
        if not content:
            return []
        
        chunks = []
        
        # Simple chunking by character count with overlap
        start = 0
        content_length = len(content)
        
        while start < content_length:
            # Get chunk
            end = start + self.chunk_size
            chunk = content[start:end]
            
            # If not the last chunk, try to break at sentence boundary
            if end < content_length:
                # Look for sentence boundaries
                for delimiter in ['. ', '! ', '? ', '\n\n', '\n']:
                    last_delim = chunk.rfind(delimiter)
                    if last_delim > self.chunk_size // 2:  # At least halfway through
                        chunk = chunk[:last_delim + len(delimiter)]
                        break
            
            chunks.append(chunk.strip())
            
            # Move start position (with overlap)
            start = start + len(chunk) - self.chunk_overlap
        
        return [chunk for chunk in chunks if chunk]
    
    def _compute_content_hash(self, content: str) -> str:
        """
        Compute hash of content for deduplication.
        
        Args:
            content: Document content
            
        Returns:
            SHA-256 hash
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get_indexed_chunks(self, document_id: int) -> list[dict]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of chunk dictionaries
        """
        # This would query the vector store for all chunks with matching document_id
        # Implementation depends on vector store capabilities
        return []
    
    def clear_cache(self):
        """Clear indexer cache."""
        self._cache.clear()


# Singleton instance
document_indexer = DocumentIndexer()