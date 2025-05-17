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
from datetime import datetime

def scan_pysnip_directory(root_path):
    """
    Scan the PySnip directory structure and build a catalog of available tools.
    
    Args:
        root_path (str): Path to the PySnip root directory
        
    Returns:
        dict: A dictionary containing the catalog structure
    """
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"PySnip root directory not found at: {root_path}")
    
    catalog = {
        "name": "PySnip Collection",
        "description": "A collection of Python scripts and utilities",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categories": [],
        "tools_count": 0,
        "root_path": root_path
    }
    
    # Ignore certain directories/patterns
    ignore_patterns = [
        r'^\..*',  # Hidden files/directories
        r'^__.*',  # Python special directories
        r'^test.*'  # Test directories
    ]
    
    # List of known categories from the JSON data
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        
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
            
            # Find Python scripts in the tool directory
            python_files = [f for f in os.listdir(tool_dir_path) 
                           if f.endswith('.py') and os.path.isfile(os.path.join(tool_dir_path, f))]
            
            if not python_files:
                continue  # Skip directories without Python files
            
            # Assume the main script is either named after the directory or the first Python file
            main_script = next((f for f in python_files if f == f"{tool_dir}.py"), python_files[0])
            
            # Find guide files (PDF, markdown, etc.)
            guide_files = [f for f in os.listdir(tool_dir_path) 
                          if any(f.endswith(ext) for ext in ['.pdf', '.md', '.txt', '.docx'])]
            
            guide_file = guide_files[0] if guide_files else None
            
            # Get file size and modification time
            script_path = os.path.join(tool_dir_path, main_script)
            file_size = os.path.getsize(script_path)
            mod_time = os.path.getmtime(script_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
            
            # Determine if script is complete (simple heuristic based on file size)
            # Placeholder scripts are very small
            is_complete = file_size > 1000  # More than 1KB
            
            tool = {
                "name": tool_dir.replace('_', ' ').title(),
                "directory": tool_dir,
                "path": f"{item}/{tool_dir}/{main_script}",
                "relative_path": f"{item}/{tool_dir}/{main_script}",
                "script": main_script,
                "guide": guide_file,
                "guide_path": f"{item}/{tool_dir}/{guide_file}" if guide_file else None,
                "complete": is_complete,
                "file_size": file_size,
                "mod_date": mod_time_str,
                "category": item
            }
            
            category["tools"].append(tool)
            catalog["tools_count"] += 1
        
        # Only add categories with tools
        if category["tools"]:
            catalog["categories"].append(category)
    
    return catalog

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

if __name__ == "__main__":
    # Test the scanner with a sample path
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "../../pysnip"  # Default test path
    
    try:
        catalog = scan_pysnip_directory(path)
        print(f"Found {catalog['tools_count']} tools in {len(catalog['categories'])} categories")
        print(json.dumps(catalog, indent=2))
    except Exception as e:
        print(f"Error: {e}")
