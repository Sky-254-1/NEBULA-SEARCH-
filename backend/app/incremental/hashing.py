"""Hashing utilities for incremental re-indexing."""

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class HashAlgorithm(str, Enum):
    """Hash algorithm enumeration."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


def _get_hash_function(algorithm: HashAlgorithm = HashAlgorithm.SHA256):
    """Get hash function for algorithm."""
    if algorithm == HashAlgorithm.SHA256:
        return hashlib.sha256
    elif algorithm == HashAlgorithm.SHA512:
        return hashlib.sha512
    elif algorithm == HashAlgorithm.BLAKE2B:
        return hashlib.blake2b
    else:
        return hashlib.sha256


def calculate_file_hash(file_path: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
    """
    Calculate hash of file content.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of file hash
    """
    hash_func = _get_hash_function(algorithm)
    sha = hash_func()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    
    return sha.hexdigest()


def calculate_string_hash(content: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
    """
    Calculate hash of string content.

    Args:
        content: String content
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of content hash
    """
    hash_func = _get_hash_function(algorithm)
    return hash_func(content.encode("utf-8")).hexdigest()


def calculate_bytes_hash(content: bytes, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
    """
    Calculate hash of bytes content.

    Args:
        content: Bytes content
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of content hash
    """
    hash_func = _get_hash_function(algorithm)
    return hash_func(content).hexdigest()


def calculate_document_hash(
    file_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
) -> str:
    """
    Calculate comprehensive document hash including content and metadata.

    Args:
        file_path: Path to document file
        metadata: Document metadata dictionary
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of document hash
    """
    hash_func = _get_hash_function(algorithm)
    sha = hash_func()
    
    # Hash file content
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    
    # Hash metadata if provided
    if metadata:
        metadata_json = json.dumps(metadata, sort_keys=True, default=str)
        sha.update(metadata_json.encode("utf-8"))
    
    return sha.hexdigest()


def calculate_metadata_hash(metadata: Dict[str, Any]) -> str:
    """
    Calculate hash of document metadata.

    Only includes searchable metadata fields:
    - title
    - description
    - author
    - category
    - tags
    - language
    - permissions
    - collections

    Args:
        metadata: Document metadata dictionary

    Returns:
        Hex digest of metadata hash
    """
    # Filter to only metadata fields that affect search
    searchable_fields = {
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "author": metadata.get("author", ""),
        "category": metadata.get("category", ""),
        "tags": metadata.get("tags", []),
        "language": metadata.get("language", ""),
        "permissions": metadata.get("permissions", {}),
        "collections": metadata.get("collections", []),
    }
    
    metadata_json = json.dumps(searchable_fields, sort_keys=True, default=str)
    return hashlib.sha256(metadata_json.encode("utf-8")).hexdigest()


def calculate_chunk_hash(content: str, chunk_index: int, chunk_metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Calculate hash for a document chunk.

    Args:
        content: Chunk text content
        chunk_index: Index position of chunk
        chunk_metadata: Optional chunk metadata

    Returns:
        Hex digest of chunk hash
    """
    hash_input = {
        "content": content,
        "chunk_index": chunk_index,
        "metadata": chunk_metadata or {},
    }
    
    hash_json = json.dumps(hash_input, sort_keys=True)
    return hashlib.sha256(hash_json.encode("utf-8")).hexdigest()


def calculate_vector_hash(embedding: list[float], chunk_id: str) -> str:
    """
    Calculate hash for vector embedding.

    Used to detect if embeddings have changed without comparing vectors directly.

    Args:
        embedding: Vector embedding list
        chunk_id: Associated chunk identifier

    Returns:
        Hex digest of vector hash
    """
    hash_input = {
        "embedding": embedding,
        "chunk_id": chunk_id,
    }
    
    hash_json = json.dumps(hash_input, sort_keys=True)
    return hashlib.sha256(hash_json.encode("utf-8")).hexdigest()


def generate_content_fingerprint(content: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> str:
    """
    Generate content fingerprint for quick comparison.

    Args:
        content: Text content
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of content fingerprint
    """
    return calculate_string_hash(content, algorithm)


@dataclass
class HashResult:
    """Result of hash calculation."""
    document_hash: str
    metadata_hash: str
    chunk_hashes: list[str]
    vector_hashes: list[str]
    content_fingerprint: str


def calculate_all_hashes(
    file_path: str,
    chunks: list[str],
    embeddings: Optional[list[list[float]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
) -> HashResult:
    """
    Calculate all hashes for a document.

    Args:
        file_path: Path to document file
        chunks: List of text chunks
        embeddings: Optional list of vector embeddings
        metadata: Optional document metadata
        algorithm: Hash algorithm to use

    Returns:
        HashResult with all calculated hashes
    """
    # Document hash (content + metadata)
    document_hash = calculate_document_hash(file_path, metadata, algorithm)
    
    # Metadata hash
    metadata_hash = calculate_metadata_hash(metadata or {})
    
    # Chunk hashes
    chunk_hashes = [
        calculate_chunk_hash(chunk, idx)
        for idx, chunk in enumerate(chunks)
    ]
    
    # Vector hashes (if embeddings provided)
    vector_hashes = []
    if embeddings:
        vector_hashes = [
            calculate_vector_hash(emb, f"chunk_{idx}")
            for idx, emb in enumerate(embeddings)
        ]
    
    # Content fingerprint (entire document text)
    content = "".join(chunks)
    content_fingerprint = generate_content_fingerprint(content, algorithm)
    
    return HashResult(
        document_hash=document_hash,
        metadata_hash=metadata_hash,
        chunk_hashes=chunk_hashes,
        vector_hashes=vector_hashes,
        content_fingerprint=content_fingerprint,
    )


def compare_hashes(old_hash: str, new_hash: str) -> bool:
    """
    Compare two hashes.

    Args:
        old_hash: Previous hash
        new_hash: Current hash

    Returns:
        True if hashes differ, False if identical
    """
    return old_hash != new_hash


def verify_file_integrity(file_path: str, expected_hash: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> bool:
    """
    Verify file integrity against expected hash.

    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use

    Returns:
        True if file hash matches expected hash
    """
    actual_hash = calculate_file_hash(file_path, algorithm)
    return actual_hash == expected_hash