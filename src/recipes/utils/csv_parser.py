"""CSV parsing utilities."""

import csv
import os
from typing import Dict, Any, Optional
import aiofiles


class CSVParser:
    """CSV parser for recipe data."""
    
    @staticmethod
    async def _read_csv_with_encoding(csv_file_path: str) -> str:
        """Read CSV file with automatic encoding detection."""
        # Try different encodings in order
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(csv_file_path, 'r', encoding=encoding, errors='strict') as file:
                    content = await file.read()
                return content
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If all encodings fail, use utf-8 with error handling
        async with aiofiles.open(csv_file_path, 'r', encoding='utf-8', errors='replace') as file:
            return await file.read()
    
    async def get_entry(self, csv_file_path: str, entry_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific entry from a CSV file."""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            content = await self._read_csv_with_encoding(csv_file_path)
                
            # Parse CSV content
            csv_reader = csv.DictReader(content.splitlines())
            rows = list(csv_reader)
            
            if entry_number < 1 or entry_number > len(rows):
                return None
            
            return rows[entry_number - 1]  # Convert to 0-based index
            
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
    
    async def get_all_entries(self, csv_file_path: str) -> list[Dict[str, Any]]:
        """Get all entries from a CSV file."""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            content = await self._read_csv_with_encoding(csv_file_path)
                
            # Parse CSV content
            csv_reader = csv.DictReader(content.splitlines())
            return list(csv_reader)
            
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
    
    async def count_entries(self, csv_file_path: str) -> int:
        """Count the number of entries in a CSV file."""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            content = await self._read_csv_with_encoding(csv_file_path)
                
            # Parse CSV content
            csv_reader = csv.DictReader(content.splitlines())
            return sum(1 for _ in csv_reader)
            
        except Exception as e:
            raise Exception(f"Error counting CSV entries: {str(e)}")
