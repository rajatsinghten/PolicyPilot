#!/usr/bin/env python3
"""
Migration script to fix document names in the embedding storage.
Converts temporary filenames (tmpXXXXXX.ext) to user-friendly names.
"""

import os
import sys
from pathlib import Path
import pickle

# Add app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.embedder import EmbeddingStorage

def migrate_document_names():
    """Migrate temporary document names to better names."""
    storage = EmbeddingStorage()
    
    # Load existing embeddings
    chunks = storage.load_embeddings()
    
    if not chunks:
        print("No embeddings found. Nothing to migrate.")
        return
    
    # Find all unique sources
    unique_sources = set(chunk.source for chunk in chunks)
    print(f"\nFound {len(unique_sources)} unique document source(s):")
    for i, source in enumerate(unique_sources, 1):
        chunk_count = sum(1 for chunk in chunks if chunk.source == source)
        print(f"  {i}. {source} ({chunk_count} chunks)")
    
    # Identify temporary names (format: tmpXXXXXX.ext)
    import re
    temp_pattern = re.compile(r'^tmp[a-z0-9]+\.\w+$')
    temp_sources = [s for s in unique_sources if temp_pattern.match(s)]
    
    if not temp_sources:
        print("\n✅ No temporary filenames found. Database is already clean.")
        return
    
    print(f"\n⚠️  Found {len(temp_sources)} temporary filename(s) to migrate:")
    for source in temp_sources:
        print(f"  - {source}")
    
    # Ask for confirmation
    print("\nOptions:")
    print("1. Auto-rename to 'policy_document_N' format")
    print("2. Provide custom names")
    print("3. Cancel migration")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "3":
        print("Migration cancelled.")
        return
    
    new_chunks = []
    
    if choice == "1":
        # Auto-rename with incrementing numbers
        for chunk in chunks:
            if chunk.source in temp_sources:
                idx = temp_sources.index(chunk.source) + 1
                extension = Path(chunk.source).suffix or ".pdf"
                new_name = f"policy_document_{idx}{extension}"
                chunk.source = new_name
            new_chunks.append(chunk)
        
        print(f"\n✅ Renamed {len(temp_sources)} document(s)")
        
    elif choice == "2":
        # Ask for custom names
        mapping = {}
        for source in temp_sources:
            new_name = input(f"\nNew name for '{source}': ").strip()
            if not new_name:
                print("  ❌ Skipped (empty name)")
                continue
            mapping[source] = new_name
        
        for chunk in chunks:
            if chunk.source in mapping:
                chunk.source = mapping[chunk.source]
            new_chunks.append(chunk)
        
        print(f"\n✅ Renamed {len(mapping)} document(s)")
    
    else:
        print("Invalid choice. Migration cancelled.")
        return
    
    # Save migrated chunks
    storage.save_embeddings(new_chunks)
    print("✅ Migration complete! Documents saved with new names.")
    print("\nNew document names:")
    new_unique_sources = set(chunk.source for chunk in new_chunks)
    for source in sorted(new_unique_sources):
        chunk_count = sum(1 for chunk in new_chunks if chunk.source == source)
        print(f"  - {source} ({chunk_count} chunks)")

if __name__ == "__main__":
    try:
        migrate_document_names()
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
