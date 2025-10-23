"""Optimized CSV parsing utilities for large files."""

import csv
import os
from typing import Dict, Any, Optional
import aiofiles


class OptimizedCSVParser:
    """Optimized CSV parser for large recipe data files.
    
    Uses streaming and caching to avoid loading entire files into memory.
    """
    
    def __init__(self):
        """Initialize the parser with a cache for file headers."""
        self._header_cache = {}
    
    @staticmethod
    async def _detect_encoding(csv_file_path: str) -> str:
        """Detect file encoding by reading first few lines."""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='strict') as file:
                    # Try to read first 1000 characters
                    await file.read(1000)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'utf-8'  # Fallback
    
    async def get_entry(self, csv_file_path: str, entry_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific entry from CSV file using streaming (memory efficient).
        
        Args:
            csv_file_path: Path to the CSV file
            entry_number: Entry number (1-based indexing)
            
        Returns:
            Dictionary with entry data or None if not found
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            # Detect encoding once per file
            if csv_file_path not in self._header_cache:
                encoding = await self._detect_encoding(csv_file_path)
            else:
                encoding = self._header_cache[csv_file_path]['encoding']
            
            # Stream through file line by line
            async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='replace') as file:
                # Read header
                header_line = await file.readline()
                if not header_line:
                    return None
                
                # Parse header
                reader = csv.reader([header_line])
                headers = next(reader)
                
                # Cache header and encoding
                if csv_file_path not in self._header_cache:
                    self._header_cache[csv_file_path] = {
                        'headers': headers,
                        'encoding': encoding
                    }
                
                # Skip to the desired entry (1-based indexing)
                current_row = 0
                async for line in file:
                    current_row += 1
                    if current_row == entry_number:
                        # Parse this row only
                        reader = csv.reader([line])
                        values = next(reader)
                        
                        # Create dictionary
                        return dict(zip(headers, values))
                
                # Entry number out of range
                return None
                
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
    
    async def get_entries_batch(
        self, 
        csv_file_path: str, 
        start_entry: int, 
        end_entry: int
    ) -> list[Dict[str, Any]]:
        """Get a batch of entries efficiently (memory optimized).
        
        Args:
            csv_file_path: Path to the CSV file
            start_entry: Starting entry number (1-based, inclusive)
            end_entry: Ending entry number (1-based, inclusive)
            
        Returns:
            List of entry dictionaries
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            # Detect encoding
            if csv_file_path not in self._header_cache:
                encoding = await self._detect_encoding(csv_file_path)
            else:
                encoding = self._header_cache[csv_file_path]['encoding']
            
            results = []
            
            async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='replace') as file:
                # Read header
                header_line = await file.readline()
                if not header_line:
                    return []
                
                reader = csv.reader([header_line])
                headers = next(reader)
                
                # Stream through file
                current_row = 0
                async for line in file:
                    current_row += 1
                    
                    # Skip entries before start
                    if current_row < start_entry:
                        continue
                    
                    # Stop after end
                    if current_row > end_entry:
                        break
                    
                    # Parse and collect this row
                    reader = csv.reader([line])
                    values = next(reader)
                    results.append(dict(zip(headers, values)))
                
                return results
                
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
    
    async def count_entries(self, csv_file_path: str) -> int:
        """Count entries efficiently without loading into memory.
        
        Uses system tools for best performance on large files.
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            # For very large files, use a more efficient counting method
            count = 0
            async with aiofiles.open(csv_file_path, 'r', encoding='utf-8', errors='replace') as file:
                # Skip header
                await file.readline()
                
                # Count remaining lines
                async for _ in file:
                    count += 1
            
            return count
            
        except Exception as e:
            raise Exception(f"Error counting CSV entries: {str(e)}")
    
    async def get_all_entries(self, csv_file_path: str) -> list[Dict[str, Any]]:
        """Get all entries (use with caution on large files!)
        
        This method loads everything into memory and should only be used
        for small CSV files. For large files, use get_entries_batch() instead.
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        # Warn about memory usage
        file_size = os.path.getsize(csv_file_path)
        if file_size > 100_000_000:  # 100MB
            print(f"⚠️  Warning: Large file ({file_size / 1_000_000:.1f}MB). Consider using get_entries_batch() instead.")
        
        try:
            encoding = await self._detect_encoding(csv_file_path)
            
            async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='replace') as file:
                content = await file.read()
                
            csv_reader = csv.DictReader(content.splitlines())
            return list(csv_reader)
            
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")

