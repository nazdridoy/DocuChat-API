import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional, Union
import uuid
from .engine import get_db_connection


def insert_document(db_path: str, document: Dict[str, Any]) -> Dict[str, str]:
    """
    Insert a document into the database
    
    Args:
        db_path: Database file path
        document: Document dictionary with id, name, type, size, and optional file_hash
        
    Returns:
        Dictionary with document ID
    """
    try:
        connection = get_db_connection(db_path)
        
        # Insert document
        stmt = connection.execute(
            """
            INSERT INTO documents (id, name, type, size, file_hash) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (document["id"], document["name"], document["type"], document["size"], document.get("file_hash"))
        )
        
        connection.commit()
        connection.close()
        
        return {"id": document["id"]}
        
    except Exception as e:
        print(f"Error inserting document: {e}")
        if connection:
            connection.close()
        raise e


def insert_chunks(db_path: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Insert document chunks into the database
    
    Args:
        db_path: Database file path
        chunks: List of chunk dictionaries with id, document_id, and content
        
    Returns:
        Dictionary with success status and count
    """
    try:
        connection = get_db_connection(db_path)
        
        # Insert chunks in a transaction
        with connection:
            for chunk in chunks:
                connection.execute(
                    """
                    INSERT INTO chunks (id, document_id, content) 
                    VALUES (?, ?, ?)
                    """,
                    (chunk["id"], chunk["document_id"], chunk["content"])
                )
        
        connection.close()
        
        return {"success": True, "count": len(chunks)}
        
    except Exception as e:
        print(f"Error inserting chunks: {e}")
        if connection:
            connection.close()
        raise e


def insert_embedding(db_path: str, embedding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert an embedding into the database
    
    Args:
        db_path: Database file path
        embedding: Embedding dictionary with chunk_id and embedding
        
    Returns:
        Dictionary with success status
    """
    try:
        connection = get_db_connection(db_path)
        
        # Get chunk rowid
        cursor = connection.execute(
            "SELECT rowid FROM chunks WHERE id = ?",
            (embedding["chunk_id"],)
        )
        chunk = cursor.fetchone()
        
        if not chunk:
            raise ValueError(f"Chunk with id {embedding['chunk_id']} not found")
            
        chunk_rowid = chunk[0]
        
        # Convert embedding to buffer
        embedding_array = np.array(embedding["embedding"], dtype=np.float32)
        embedding_buffer = embedding_array.tobytes()
        
        # Insert embedding
        connection.execute(
            """
            INSERT INTO vss_embeddings (rowid, embedding) 
            VALUES (?, ?)
            """,
            (chunk_rowid, embedding_buffer)
        )
        
        connection.commit()
        connection.close()
        
        return {"success": True}
        
    except Exception as e:
        print(f"Error inserting embedding: {e}")
        if connection:
            connection.close()
        raise e


def search_similar_embeddings(
    db_path: str, 
    embedding_vector: List[float], 
    limit: int = 20, 
    override_threshold: Optional[float] = None,
    similarity_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search for similar embeddings in the database
    
    Args:
        db_path: Database file path
        embedding_vector: Query embedding vector
        limit: Maximum number of results
        override_threshold: Optional threshold to override default
        similarity_threshold: Default similarity threshold
        
    Returns:
        List of similar chunks with similarity scores
    """
    try:
        connection = get_db_connection(db_path)
        
        # Convert embedding to buffer
        embedding_array = np.array(embedding_vector, dtype=np.float32)
        embedding_buffer = embedding_array.tobytes()
        
        # Set threshold
        threshold = override_threshold if override_threshold is not None else similarity_threshold
        
        # Execute search query - updated to use vec_search instead of vss_search
        # Use vec_search with vector function instead of passing embedding directly
        cursor = connection.execute(
            """
            WITH matches AS (
                SELECT
                    rowid,
                    vec_cosine_similarity(embedding, ?) as similarity
                FROM vss_embeddings
                ORDER BY similarity DESC
                LIMIT ?
            )
            SELECT
                c.id as chunk_id,
                c.content,
                c.document_id,
                m.similarity,
                v.embedding
            FROM matches m
            JOIN chunks c ON c.rowid = m.rowid
            JOIN vss_embeddings v ON v.rowid = m.rowid
            WHERE m.similarity >= ?
            """,
            (embedding_buffer, limit, threshold)
        )
        
        # Process results
        results = []
        for row in cursor.fetchall():
            chunk_id, content, document_id, similarity, embedding_blob = row
            
            # Convert embedding blob back to vector
            embedding_vector = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
            
            results.append({
                "chunk_id": chunk_id,
                "content": content,
                "document_id": document_id,
                "similarity": similarity,
                "embedding": embedding_vector
            })
        
        connection.close()
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        print(f"Found {len(results)} similar chunks above threshold {threshold}. " +
              f"Top similarity score: {results[0]['similarity'] if results else 'N/A'}")
        
        return results
        
    except Exception as e:
        print(f"Error searching similar embeddings: {e}")
        if connection:
            connection.close()
        raise e


def get_documents(db_path: str) -> List[Dict[str, Any]]:
    """
    Get all documents in the database
    
    Args:
        db_path: Database file path
        
    Returns:
        List of document dictionaries
    """
    try:
        connection = get_db_connection(db_path)
        
        cursor = connection.execute(
            "SELECT id, name, type, size, file_hash, created_at FROM documents ORDER BY created_at DESC"
        )
        
        documents = []
        for row in cursor.fetchall():
            id, name, type, size, file_hash, created_at = row
            documents.append({
                "id": id,
                "name": name,
                "type": type,
                "size": size,
                "file_hash": file_hash,
                "created_at": created_at
            })
        
        connection.close()
        
        return documents
        
    except Exception as e:
        print(f"Error getting documents: {e}")
        if connection:
            connection.close()
        raise e


def delete_document(db_path: str, document_id: str) -> Dict[str, bool]:
    """
    Delete a document and its chunks/embeddings from the database
    
    Args:
        db_path: Database file path
        document_id: Document ID to delete
        
    Returns:
        Dictionary with success status
    """
    try:
        connection = get_db_connection(db_path)
        
        # Execute in a transaction
        with connection:
            # Get chunk rowids to delete embeddings
            cursor = connection.execute(
                "SELECT rowid FROM chunks WHERE document_id = ?",
                (document_id,)
            )
            
            rowids = [row[0] for row in cursor.fetchall()]
            
            # Delete embeddings for these chunks
            if rowids:
                placeholders = ','.join(['?' for _ in rowids])
                connection.execute(
                    f"DELETE FROM vss_embeddings WHERE rowid IN ({placeholders})",
                    rowids
                )
            
            # Delete document (will cascade to chunks)
            connection.execute(
                "DELETE FROM documents WHERE id = ?",
                (document_id,)
            )
        
        connection.close()
        
        return {"success": True}
        
    except Exception as e:
        print(f"Error deleting document: {e}")
        if connection:
            connection.close()
        raise e


def find_document_by_hash(db_path: str, file_hash: str) -> Optional[Dict[str, Any]]:
    """
    Find a document by its hash
    
    Args:
        db_path: Database file path
        file_hash: File hash to search for
        
    Returns:
        Document dictionary or None if not found
    """
    try:
        connection = get_db_connection(db_path)
        
        cursor = connection.execute(
            "SELECT id, name, type, size, created_at FROM documents WHERE file_hash = ? LIMIT 1",
            (file_hash,)
        )
        
        row = cursor.fetchone()
        connection.close()
        
        if row:
            id, name, type, size, created_at = row
            return {
                "id": id,
                "name": name,
                "type": type,
                "size": size,
                "file_hash": file_hash,
                "created_at": created_at
            }
        
        return None
        
    except Exception as e:
        print(f"Error finding document by hash: {e}")
        if connection:
            connection.close()
        raise e 