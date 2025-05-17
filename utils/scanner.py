#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner module for PySnip Web Interface
---------------------------------------
Scans the PySnip directory structure to build a catalog of available tools.
Extracts basic metadata from directory names and file structures.
"""

import os
import re
import json
import logging
from datetime import datetime
import hashlib
import time

# Set up logger
logger = logging.getLogger(__name__)

class DirectoryScanner:
    """Class for scanning directories and managing scan state"""
    
    def __init__(self, root_path):
        self.root_path = root_path
        self.last_scan_time = 0
        self._catalog = None
        self._cache_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "cache", 
            "catalog_cache.json"
        )
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
    
    def scan(self, force=False):
        """Scan the directory and return the catalog, using cache if applicable"""
        if not force and self._catalog and time.time() - self.last_scan_time < 3600:
            return self._catalog
        
        # Try to load from cache first if not forcing a rescan
        if not force and os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, 'r') as f:
                    cached_catalog = json.load(f)
                
                # Verify cache is for the same root path
                if cached_catalog.get('root_path') == self.root_path:
                    # Check if any files have been modified since the cache was created
                    cache_time = cached_catalog.get('cache_time', 0)
                    if not self._has_modified_files(self.root_path, cache_time):
                        logger.info(f"Using catalog from cache (created {datetime.fromtimestamp(cache_time)})")
                        self._catalog = cached_catalog
                        self.last_scan_time = time.time()
                        return self._catalog
            except Exception as e:
                logger.warning(f"Error loading catalog from cache: {e}")
        
        # Perform a fresh scan
        logger.info(f"Performing fresh scan of {self.root_path}")
        self._catalog = self._scan_directory()
        self.last_scan_time = time.time()
        
        # Save to cache
        try:
            self._catalog['cache_time'] = self.last_scan_time
            with open(self._cache_file, 'w') as f:
                json.dump(self._catalog, f)
            logger.info(f"Saved catalog to cache")
        except Exception as e:
            logger.warning(f"Error saving catalog to cache: {e}")
        
        return self._catalog
    
    def _has_modified_files(self, dir_path, timestamp):
        """Check if any files in the directory have been modified since the timestamp"""
        if not os.path.exists(dir_path):
            return False
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(file_path) > timestamp:
                        return True
                except Exception:
                    pass
        
        return False
    
    def _scan_directory(self):
        """Perform the actual directory scan"""
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"PySnip root directory not found at: {self.root_path}")
        
        catalog = {
            "name": "PySnip Collection",
            "description": "A collection of Python scripts and utilities",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "categories": [],
            "tools_count": 0,
            "root_path": self.root_path,
            "scan_time": time.time()
        }
        
        # Ignore certain directories/patterns
        ignore_patterns = [
            r'^\..*',  # Hidden files/directories
            r'^__.*',  # Python special directories
            r'^test.*',  # Test directories
            r'^venv.*',  # Virtual environments
            r'^node_modules.*',  # Node.js modules
            r'^cache.*',  # Cache directories
        ]
        
        # List of known categories from the JSON data
        for item in os.listdir(self.root_path):
            item_path = os.path.join(self.root_path, item)
            
            # Skip files at root level and directories matching ignore patterns
            if not os.path.isdir(item_path) or any(re.match(pattern, item) for pattern in ignore_patterns):
                continue
            
            # Process category
            category = {
                "name": item,
                "display_name": item.replace('_', ' ').title(),
                "path": item,
                "description": get_category_description(item),
                "tools": [],
                "image": f"{item}.png"  # Placeholder for category image
            }
            
            # Scan subdirectories for tools
            for tool_dir in os.listdir(item_path):
                tool_dir_path = os.path.join(item_path, tool_dir)
                
                if not os.path.isdir(tool_dir_path) or any(re.match(pattern, tool_dir) for pattern in ignore_patterns):
                    continue
                
                try:
                    # Find Python scripts in the tool directory
                    python_files = [f for f in os.listdir(tool_dir_path) 
                                  if f.endswith('.py') and os.path.isfile(os.path.join(tool_dir_path, f))]
                    
                    if not python_files:
                        continue  # Skip directories without Python files
                    
                    # Determine main script with better heuristics
                    main_script = self._find_main_script(tool_dir_path, tool_dir, python_files)
                    
                    # Find guide files (PDF, markdown, etc.)
                    guide_files = [f for f in os.listdir(tool_dir_path) 
                                  if any(f.endswith(ext) for ext in ['.pdf', '.md', '.txt', '.docx', '.html'])]
                    
                    guide_file = guide_files[0] if guide_files else None
                    
                    # Find additional resources
                    resource_files = [f for f in os.listdir(tool_dir_path)
                                    if any(f.endswith(ext) for ext in ['.csv', '.json', '.yaml', '.yml', '.xml', '.ini', '.cfg'])]
                    
                    # Get file size and modification time
                    script_path = os.path.join(tool_dir_path, main_script)
                    file_size = os.path.getsize(script_path)
                    mod_time = os.path.getmtime(script_path)
                    mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
                    
                    # Hash the file content for cache busting
                    file_hash = self._hash_file(script_path)
                    
                    # Determine if script is complete (better heuristics)
                    is_complete = self._is_tool_complete(script_path, file_size)
                    
                    tool = {
                        "name": tool_dir.replace('_', ' ').title(),
                        "directory": tool_dir,
                        "path": f"{item}/{tool_dir}/{main_script}",
                        "relative_path": f"{item}/{tool_dir}/{main_script}",
                        "script": main_script,
                        "guide": guide_file,
                        "guide_path": f"{item}/{tool_dir}/{guide_file}" if guide_file else None,
                        "resources": resource_files,
                        "complete": is_complete,
                        "file_size": file_size,
                        "mod_date": mod_time_str,
                        "timestamp": mod_time,
                        "hash": file_hash,
                        "category": item,
                        "all_scripts": python_files
                    }
                    
                    category["tools"].append(tool)
                    catalog["tools_count"] += 1
                
                except Exception as e:
                    logger.warning(f"Error processing tool directory {tool_dir_path}: {e}")
            
            # Only add categories with tools
            if category["tools"]:
                catalog["categories"].append(category)
        
        return catalog
    
    def _find_main_script(self, dir_path, dir_name, python_files):
        """Find the main script in a directory using better heuristics"""
        # 1. Look for script with same name as directory
        dir_script = f"{dir_name}.py"
        if dir_script in python_files:
            return dir_script
        
        # 2. Look for common main script names
        common_names = ['main.py', 'app.py', 'run.py', 'cli.py', 'tool.py']
        for name in common_names:
            if name in python_files:
                return name
        
        # 3. Look for script with most content (likely the main one)
        if len(python_files) > 1:
            largest_script = max(python_files, key=lambda f: os.path.getsize(os.path.join(dir_path, f)))
            return largest_script
        
        # 4. Fallback to first script
        return python_files[0]
    
    def _is_tool_complete(self, script_path, file_size):
        """Determine if a tool is complete using better heuristics"""
        # Simple size check as a starting point
        if file_size < 1000:  # Less than 1KB
            return False
        
        try:
            # Check for placeholder markers in the content
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read just the beginning
                
                # Check for common placeholder patterns
                if 'TODO' in content and 'implement' in content.lower():
                    return False
                if 'PLACEHOLDER' in content:
                    return False
                if '# This is a placeholder' in content:
                    return False
            
            # More sophisticated checks could be added here
            return True
        except Exception:
            # If we can't read the file, use size heuristic
            return file_size > 1000
    
    def _hash_file(self, file_path):
        """Create a hash of the file content for cache busting"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return str(int(time.time()))  # Fallback to timestamp

# Global scanner instance
_scanner = None

def scan_pysnip_directory(root_path, force=False):
    """
    Scan the PySnip directory structure and build a catalog of available tools.
    Uses a singleton scanner instance for caching.
    
    Args:
        root_path (str): Path to the PySnip root directory
        force (bool): Force a fresh scan even if cached results are available
        
    Returns:
        dict: A dictionary containing the catalog structure
    """
    global _scanner
    if _scanner is None or _scanner.root_path != root_path:
        _scanner = DirectoryScanner(root_path)
    
    return _scanner.scan(force=force)

def get_category_description(category_name):
    """
    Get a description for a category based on its name.
    
    Args:
        category_name (str): The name of the category
        
    Returns:
        str: A description of the category
    """
    descriptions = {
        "automation": "Tools for automating repetitive tasks and workflows.",
        "creative": "Utilities for creative projects and content generation.",
        "data_processing": "Tools for processing, analyzing, and visualizing data.",
        "dev_tools": "Utilities for software development and programming.",
        "education": "Educational tools and learning aids.",
        "file_management": "Tools for managing, organizing, and manipulating files.",
        "finance": "Financial calculators and tracking tools.",
        "gaming": "Gaming-related utilities and tools.",
        "hardware_iot": "Tools for hardware and IoT device interaction.",
        "multimedia": "Utilities for working with audio, video, and images.",
        "networking": "Tools for network monitoring, testing, and analysis.",
        "security": "Security-related utilities and tools.",
        "system_tools": "System monitoring and management utilities.",
        "utility": "General-purpose utility tools.",
        "web_api_tools": "Tools for working with web services and APIs."
    }
    
    return descriptions.get(category_name, "A collection of Python utilities.")

def get_category_details(catalog, category_name):
    """
    Get details for a specific category from the catalog.
    
    Args:
        catalog (dict): The PySnip catalog
        category_name (str): The name of the category to retrieve
        
    Returns:
        dict: Details of the category, or None if not found
    """
    if not catalog or not catalog.get('categories'):
        return None
        
    for category in catalog["categories"]:
        if category["path"] == category_name:
            return category
    return None

def get_tool_details(catalog, tool_path):
    """
    Get details for a specific tool from the catalog.
    
    Args:
        catalog (dict): The PySnip catalog
        tool_path (str): The path to the tool to retrieve
        
    Returns:
        dict: Details of the tool, or None if not found
    """
    if not catalog or not catalog.get('categories'):
        return None
        
    # Extract the category and tool directory from the path
    parts = tool_path.split('/')
    if len(parts) < 3:
        return None
    
    category_name = parts[0]
    tool_dir = parts[1]
    
    category = get_category_details(catalog, category_name)
    if not category:
        return None
    
    for tool in category["tools"]:
        if tool["directory"] == tool_dir:
            return tool
    
    return None

def get_related_tools(catalog, category_name, count=5):
    """
    Get related tools for a specific category.
    
    Args:
        catalog (dict): The PySnip catalog
        category_name (str): The name of the category
        count (int): Maximum number of tools to return
        
    Returns:
        list: List of related tools
    """
    if not catalog or not catalog.get('categories'):
        return []
        
    category = get_category_details(catalog, category_name)
    if not category:
        return []
    
    # Sort tools by completion status and modification date
    sorted_tools = sorted(
        category["tools"],
        key=lambda x: (x.get('complete', False), x.get('timestamp', 0)),
        reverse=True
    )
    
    return sorted_tools[:count]

if __name__ == "__main__":
    # Test the scanner with a sample path
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "../../pysnip"  # Default test path
    
    try:
        catalog = scan_pysnip_directory(path, force=True)
        print(f"Found {catalog['tools_count']} tools in {len(catalog['categories'])} categories")
        
        # Save catalog to JSON for inspection
        output_file = "catalog_output.json"
        with open(output_file, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        print(f"Saved catalog to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
