"""CSV parsing utilities - optimized for large files."""

import csv
import os
from typing import Dict, Any, Optional
import aiofiles


class CSVParser:
    """CSV parser for recipe data - optimized for large files like Stromberg (2.2GB)."""
    
    def __init__(self):
        """Initialize parser with encoding cache."""
        self._encoding_cache = {}
    
    async def _detect_encoding(self, csv_file_path: str) -> str:
        """Detect file encoding efficiently by sampling."""
        if csv_file_path in self._encoding_cache:
            return self._encoding_cache[csv_file_path]
        
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='strict') as file:
                    # Sample first 10KB instead of entire file
                    await file.read(10240)
                self._encoding_cache[csv_file_path] = encoding
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Fallback
        self._encoding_cache[csv_file_path] = 'utf-8'
        return 'utf-8'
    
    async def get_entry(self, csv_file_path: str, entry_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific entry using streaming (memory efficient).
        
        Streams through file line-by-line instead of loading entire file into memory.
        This is crucial for large files like Stromberg (2.2GB).
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            encoding = await self._detect_encoding(csv_file_path)
            
            # Stream through file line by line
            async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='replace') as file:
                # Read header
                header_line = await file.readline()
                if not header_line:
                    return None
                
                # Parse header
                reader = csv.reader([header_line])
                headers = next(reader)
                
                # Stream to the desired entry
                current_row = 0
                async for line in file:
                    current_row += 1
                    if current_row == entry_number:
                        # Parse only this row
                        reader = csv.reader([line])
                        values = next(reader)
                        return dict(zip(headers, values))
                
                return None  # Entry not found
                
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
            csv_file_path: Path to CSV file
            start_entry: Starting entry (1-based, inclusive)
            end_entry: Ending entry (1-based, inclusive)
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            encoding = await self._detect_encoding(csv_file_path)
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
                    
                    if current_row < start_entry:
                        continue
                    if current_row > end_entry:
                        break
                    
                    reader = csv.reader([line])
                    values = next(reader)
                    results.append(dict(zip(headers, values)))
                
                return results
                
        except Exception as e:
            raise Exception(f"Error parsing CSV batch: {str(e)}")
    
    async def get_all_entries(self, csv_file_path: str) -> list[Dict[str, Any]]:
        """Get all entries (WARNING: Use with caution on large files!).
        
        This loads entire file into memory. For large files (>100MB), 
        use get_entries_batch() instead.
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        # Warn about large files
        file_size = os.path.getsize(csv_file_path)
        if file_size > 100_000_000:
            print(f"⚠️  Warning: Large file ({file_size / 1_000_000:.1f}MB). This may use significant memory.")
        
        try:
            encoding = await self._detect_encoding(csv_file_path)
            
            async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='replace') as file:
                # Read header
                header_line = await file.readline()
                reader = csv.reader([header_line])
                headers = next(reader)
                
                # Read all rows
                results = []
                async for line in file:
                    reader = csv.reader([line])
                    values = next(reader)
                    results.append(dict(zip(headers, values)))
                
                return results
            
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
    
    async def count_entries(self, csv_file_path: str) -> int:
        """Count entries efficiently without loading into memory."""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            encoding = await self._detect_encoding(csv_file_path)
            count = 0
            
            async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='replace') as file:
                await file.readline()  # Skip header
                async for _ in file:
                    count += 1
            
            return count
            
        except Exception as e:
            raise Exception(f"Error counting CSV entries: {str(e)}")
