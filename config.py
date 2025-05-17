#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySnip Explorer Configuration
----------------------------
Configuration settings for the PySnip Explorer web interface.
"""

import os
from pathlib import Path

# Root directory of PySnip collection
# Change this to match your PySnip root directory path
PYSNIP_ROOT = "/sdcard/1dd1/projects/personal/current/pysnip"

# Application settings
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'development-key-change-in-production')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# Custom static path
CUSTOM_STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')

# Tool execution settings
MAX_EXECUTION_TIME = 60  # Maximum execution time in seconds
MAX_OUTPUT_SIZE = 1024 * 1024  # Maximum output size in bytes (1MB)
PROHIBITED_COMMANDS = ['rm', 'del', 'format', 'mkfs', 'dd']

# User settings
ENABLE_EXECUTIONS = True  # Set to False to disable tool executions
ENABLE_SOURCE_VIEW = True  # Set to False to disable source code viewing

# Filesystem settings
TEMP_DIR = Path(os.environ.get('TEMP_DIR', '/tmp/pysnip-explorer'))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Security settings
ALLOWED_EXTENSIONS = {'py', 'txt', 'csv', 'json', 'md', 'yml', 'yaml', 'ini', 'cfg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

# UI settings
ITEMS_PER_PAGE = 12
RECENT_TOOLS_COUNT = 10
FEATURED_TOOLS_COUNT = 6

# Template helper functions
def get_category_icon(category_name):
    """Get icon for a category"""
    icons = {
        'automation': 'robot',
        'creative': 'paint-brush',
        'data_processing': 'database',
        'dev_tools': 'code',
        'education': 'graduation-cap',
        'file_management': 'folder',
        'finance': 'chart-line',
        'gaming': 'gamepad', 
        'hardware_iot': 'microchip',
        'multimedia': 'photo-video',
        'networking': 'network-wired',
        'security': 'shield-alt',
        'system_tools': 'desktop',
        'utility': 'tools',
        'web_api_tools': 'globe'
    }
    return icons.get(category_name, 'puzzle-piece')

def format_size(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_completed_count(catalog):
    """Get count of completed tools"""
    count = 0
    for category in catalog.get('categories', []):
        for tool in category.get('tools', []):
            if tool.get('complete', False):
                count += 1
    return count

def get_days_since_update(catalog):
    """Get days since last update"""
    from datetime import datetime
    most_recent = datetime.now()
    for category in catalog.get('categories', []):
        for tool in category.get('tools', []):
            tool_date = datetime.strptime(tool.get('mod_date', '2000-01-01'), '%Y-%m-%d')
            if tool_date > most_recent:
                most_recent = tool_date
    
    days = (datetime.now() - most_recent).days
    return max(0, days)

def get_recent_tools(catalog, count=RECENT_TOOLS_COUNT):
    """Get most recently updated tools"""
    all_tools = []
    for category in catalog.get('categories', []):
        all_tools.extend(category.get('tools', []))
    
    # Sort by modification date (latest first)
    from datetime import datetime
    sorted_tools = sorted(
        all_tools,
        key=lambda x: datetime.strptime(x.get('mod_date', '2000-01-01'), '%Y-%m-%d'),
        reverse=True
    )
    
    return sorted_tools[:count]

def get_featured_tools(catalog, count=FEATURED_TOOLS_COUNT):
    """Get featured tools based on completion status and size"""
    all_tools = []
    for category in catalog.get('categories', []):
        all_tools.extend(category.get('tools', []))
    
    # Sort by completion status and file size
    sorted_tools = sorted(
        all_tools,
        key=lambda x: (x.get('complete', False), x.get('file_size', 0)),
        reverse=True
    )
    
    return sorted_tools[:count]

def get_top_categories(catalog, count=5):
    """Get top categories based on number of tools"""
    categories = catalog.get('categories', [])
    
    # Sort by number of tools
    sorted_categories = sorted(
        categories,
        key=lambda x: len(x.get('tools', [])),
        reverse=True
    )
    
    return sorted_categories[:count]

def get_tool_description(tool):
    """Get a description for a tool"""
    return f"A Python utility for {tool['name'].lower()} operations"

def get_tool_icon(tool):
    """Get icon for a tool based on its category"""
    return get_category_icon(tool.get('category', 'utility'))

# Jinja2 context processor to inject template globals
def inject_template_globals():
    """Inject global variables into templates"""
    return dict(
        get_category_icon=get_category_icon,
        format_size=format_size,
        get_completed_count=get_completed_count,
        get_days_since_update=get_days_since_update,
        get_recent_tools=get_recent_tools,
        get_featured_tools=get_featured_tools,
        get_top_categories=get_top_categories,
        get_tool_description=get_tool_description,
        get_tool_icon=get_tool_icon
    )
