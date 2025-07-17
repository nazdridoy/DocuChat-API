import sqlite3
import os
import numpy as np
from typing import List, Optional, Tuple
import sqlite_vec
from ..config import SessionConfig
import traceback

# Constants
DEFAULT_EMBEDDING_DIMENSIONS = 384  # Default if not specified


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Create a SQLite database connection with WAL mode enabled
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        SQLite connection object
    """
    try:
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Check if path is writable
        if os.path.exists(db_path):
            if not os.access(db_path, os.W_OK):
                raise PermissionError(f"No write permission for database file: {db_path}")
        elif db_dir and not os.access(db_dir, os.W_OK):
            raise PermissionError(f"No write permission for directory: {db_dir}")
        
        # Connect to the database with extension loading enabled
        try:
            connection = sqlite3.connect(db_path, isolation_level=None)
            connection.enable_load_extension(True)
        except AttributeError:
            # If enable_load_extension is not available, try to connect differently
            print("Warning: SQLite extension loading not available")
            connection = sqlite3.connect(db_path)
            
            # Try an alternative approach
            try:
                connection.execute("SELECT load_extension(?)", (sqlite_vec.loadable_path(),))
            except Exception as e:
                print(f"Cannot load SQLite extensions: {e}")
                # Continue without vector search capability
        
        # Enable foreign keys
        connection.execute("PRAGMA foreign_keys = ON")
        
        # Enable WAL mode for better concurrency
        connection.execute("PRAGMA journal_mode = WAL")
        
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"Database path: {db_path}")
        traceback.print_exc()
        raise e


def initialize_database_without_vec(connection: sqlite3.Connection) -> None:
    """
    Initialize basic tables without vector search
    """
    # Create documents table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            size INTEGER NOT NULL,
            file_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chunks table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)


def initialize_database(connection: sqlite3.Connection, dimensions: int) -> None:
    """
    Initialize database tables if they don't exist
    
    Args:
        connection: SQLite connection
        dimensions: Embedding dimensions for vector search
    """
    try:
        # Create basic tables
        initialize_database_without_vec(connection)
        
        # Print available modules in sqlite_vec
        available_modules = dir(sqlite_vec)
        print(f"Available modules in sqlite_vec: {available_modules}")
        
        # Get the path to the loadable extension
        extension_path = sqlite_vec.loadable_path()
        print(f"Extension path: {extension_path}")
        
        # Try several approaches to load the sqlite-vec extension
        try:
            print("Loading sqlite_vec extension...")
            
            # Try direct loading
            try:
                print("Trying direct load...")
                sqlite_vec.load(connection)
                print("Successfully loaded sqlite_vec extension directly")
            except Exception as e:
                print(f"Direct load failed: {e}")
                
                # Try alternate loading method
                try:
                    print("Trying alternate loading...")
                    connection.execute("SELECT load_extension(?)", (extension_path,))
                    print("Successfully loaded sqlite_vec extension with alternate method")
                except Exception as e:
                    print(f"Alternate loading failed: {e}")
                    raise e
                
        except Exception as e:
            print(f"Error loading sqlite_vec: {e}")
            traceback.print_exc()
            
            # For now, proceed without vector search capability
            print("WARNING: Proceeding without vector search capability")
            return
        
        # Create vector search virtual table
        try:
            print(f"Creating vector search table with dimensions: {dimensions}")
            # Update syntax based on sqlite-vec documentation - use float[dimensions]
            connection.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vss_embeddings USING vec0(
                    embedding float[{dimensions}]
                )
            """)
            print("Successfully created vector search table")
        except Exception as e:
            print(f"Error creating vector search table: {e}")
            traceback.print_exc()
            
            # For now, proceed without vector search capability
            print("WARNING: Proceeding without vector search capability")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()
        raise e


async def test_db_connection(db_path: str, embedding_dimensions: Optional[int] = None) -> int:
    """
    Test database connection and initialize tables if needed
    
    Args:
        db_path: Path to the SQLite database file
        embedding_dimensions: Optional embedding dimensions to use
        
    Returns:
        The embedding dimensions used for the database
    """
    # Use provided dimensions or default
    dimensions = embedding_dimensions or DEFAULT_EMBEDDING_DIMENSIONS
    
    try:
        # Connect to the database
        print(f"Connecting to database at: {db_path}")
        connection = get_db_connection(db_path)
        
        # Check if database is already initialized
        try:
            # First check for documents table
            cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            if not cursor.fetchone():
                # Documents table doesn't exist, initialize database
                print(f"Initializing database at: {db_path} with embedding dimensions: {dimensions}")
                initialize_database(connection, dimensions)
            else:
                # Then check for vss_embeddings
                try:
                    cursor = connection.execute("SELECT * FROM vss_embeddings LIMIT 1")
                    cursor.fetchall()
                    print("Vector search is available")
                except sqlite3.OperationalError:
                    # Vector table doesn't exist, try to initialize it
                    print("Vector search table not found, trying to initialize")
                    initialize_database(connection, dimensions)
        except sqlite3.OperationalError as e:
            print(f"Error checking tables: {e}")
            # Initialize database anyway
            initialize_database(connection, dimensions)
            
        connection.close()
        return dimensions
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()
        
        # For testing purposes, return dimensions anyway
        print("WARNING: Returning default dimensions without full database initialization")
        return dimensions


class Database:
    """Database wrapper for DocuChat Python API"""
    
    def __init__(self, db_path: str, embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS):
        """
        Initialize database connection
        
        Args:
            db_path: Path to the SQLite database file
            embedding_dimensions: Embedding dimensions for vector search
        """
        self.db_path = db_path
        self.embedding_dimensions = embedding_dimensions
        
        # Create connection
        self.connection = get_db_connection(db_path)
        
        # Initialize database tables
        initialize_database(self.connection, embedding_dimensions)
        
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            
    def __enter__(self):
        """Context manager enter method"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit method"""
        self.close() 