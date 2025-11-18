#!/usr/bin/env python3
"""Data storage utilities for scraped quotes."""
import json
import os
from typing import List, Dict


class DataStore:
    """Handles saving and managing scraped data."""
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize data store.
        
        Args:
            output_dir: Directory to save data files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def save_to_json(self, data: List[Dict], filename: str):
        """
        Save data to JSON file.
        
        Args:
            data: List of dictionaries to save
            filename: Output filename
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(data)} items to {filepath}")
    
    def load_from_json(self, filename: str) -> List[Dict]:
        """
        Load data from JSON file.
        
        Args:
            filename: Input filename
            
        Returns:
            List of dictionaries
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    @staticmethod
    def get_unique_values(data: List[Dict], key: str) -> List[str]:
        """
        Get unique values for a specific key across all items.
        
        Args:
            data: List of dictionaries
            key: Key to extract values from
            
        Returns:
            Sorted list of unique values
        """
        values = set()
        for item in data:
            value = item.get(key)
            if isinstance(value, list):
                values.update(value)
            elif value:
                values.add(value)
        return sorted(values)
    
    @staticmethod
    def get_authors(quotes: List[Dict]) -> List[str]:
        """Get unique list of authors from quotes."""
        return DataStore.get_unique_values(quotes, 'author')
    
    @staticmethod
    def get_all_tags(quotes: List[Dict]) -> List[str]:
        """Get unique list of all tags from quotes."""
        return DataStore.get_unique_values(quotes, 'tags')
