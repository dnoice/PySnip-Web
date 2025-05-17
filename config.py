#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySnip Explorer Configuration
----------------------------
Configuration settings for the PySnip Explorer web interface.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import datetime
import platform

# Environment configuration
ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = ENV == 'development' or os.environ.get('DEBUG', 'False').lower() == 'true'

# Root directory of PySnip collection
# Change this to match your PySnip root directory path
PYSNIP_ROOT = os.environ.get('PYSNIP_ROOT', '/sdcard/1dd1/projects/personal/current/pysnip')

# Ensure the path exists
if not os.path.exists(PYSNIP_ROOT):
    logging.warning(f"PySnip root directory not found at: {PYSNIP_ROOT}")
    # Try to find a suitable default path
    possible_paths = [
        os.path.join(os.path.expanduser('~'), 'pysnip'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pysnip'),
        '/sdcard/pysnip',
        '/sdcard/1dd1/projects/pysnip'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            PYSNIP_ROOT = path
            logging.info(f"Found PySnip directory at: {PYSNIP_ROOT}")
            break

# Application settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'development-key-change-in-production')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
for directory in [CACHE_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.path.join(LOG_DIR, 'pysnip_explorer.log')

# Custom static path
CUSTOM_STATIC_PATH = os.path.join(STATIC_DIR, 'images')

# Tool execution settings
MAX_EXECUTION_TIME = int(os.environ.get('MAX_EXECUTION_TIME', 60))  # Maximum execution time in seconds
MAX_OUTPUT_SIZE = int(os.environ.get('MAX_OUTPUT_SIZE', 1024 * 1024))  # Maximum output size in bytes (1MB)
MAX_MEMORY_USAGE = int(os.environ.get('MAX_MEMORY_USAGE', 512 * 1024 * 1024))  # Maximum memory usage (512MB)
PROHIBITED_COMMANDS = os.environ.get('PROHIBITED_COMMANDS', 'rm,del,format,mkfs,dd').split(',')

# User settings
ENABLE_EXECUTIONS = os.environ.get('ENABLE_EXECUTIONS', 'True').lower() == 'true'
ENABLE_SOURCE_VIEW = os.environ.get('ENABLE_SOURCE_VIEW', 'True').lower() == 'true'
ENABLE_ADMIN = os.environ.get('ENABLE_ADMIN', 'False').lower() == 'true'

# Security settings
ALLOWED_EXTENSIONS = {'py', 'txt', 'csv', 'json', 'md', 'yml', 'yaml', 'ini', 'cfg'}
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max upload size
RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 60))  # requests per minute

# Caching settings
CATALOG_CACHE_TIME = int(os.environ.get('CATALOG_CACHE_TIME', 3600))  # Cache catalog for 1 hour
CATALOG_SCAN_INTERVAL = int(os.environ.get('CATALOG_SCAN_INTERVAL', 3600))  # Rescan catalog every hour
USE_CATALOG_CACHE = os.environ.get('USE_CATALOG_CACHE', 'True').lower() == 'true'

# UI settings
ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 12))
RECENT_TOOLS_COUNT = int(os.environ.get('RECENT_TOOLS_COUNT', 10))
FEATURED_TOOLS_COUNT = int(os.environ.get('FEATURED_TOOLS_COUNT', 6))

# Mobile support
IS_MOBILE_DEVICE = platform.machine() in ['aarch64', 'armv7l', 'armv8l'] or 'Android' in platform.version()
MOBILE_REDIRECT = os.environ.get('MOBILE_REDIRECT', 'False').lower() == 'true'

# System information
SYSTEM_INFO = {
    'os': platform.system(),
    'python_version': platform.python_version(),
    'platform': platform.platform(),
    'node': platform.node(),
    'processor': platform.processor()
}

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
    if not catalog:
        return 0
        
    count = 0
    for category in catalog.get('categories', []):
        for tool in category.get('tools', []):
            if tool.get('complete', False):
                count += 1
    return count

def get_days_since_update(catalog):
    """Get days since last update"""
    if not catalog:
        return 0
        
    most_recent = datetime.datetime.min
    for category in catalog.get('categories', []):
        for tool in category.get('tools', []):
            try:
                tool_date = datetime.datetime.strptime(tool.get('mod_date', '2000-01-01'), '%Y-%m-%d')
                if tool_date > most_recent:
                    most_recent = tool_date
            except (ValueError, TypeError):
                continue
    
    days = (datetime.datetime.now() - most_recent).days
    return max(0, days)

def get_recent_tools(catalog, count=None):
    """Get most recently updated tools"""
    if not catalog:
        return []
        
    if count is None:
        count = RECENT_TOOLS_COUNT
        
    all_tools = []
    for category in catalog.get('categories', []):
        all_tools.extend(category.get('tools', []))
    
    # Sort by modification date (latest first)
    try:
        sorted_tools = sorted(
            all_tools,
            key=lambda x: datetime.datetime.strptime(x.get('mod_date', '2000-01-01'), '%Y-%m-%d'),
            reverse=True
        )
    except (ValueError, TypeError):
        # Fallback if dates are not valid
        sorted_tools = all_tools
    
    return sorted_tools[:count]

def get_featured_tools(catalog, count=None):
    """Get featured tools based on completion status and size"""
    if not catalog:
        return []
        
    if count is None:
        count = FEATURED_TOOLS_COUNT
        
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
    if not catalog:
        return []
        
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
    if not tool:
        return ""
        
    default_desc = f"A Python utility for {tool['name'].lower()} operations"
    
    # Try to get a better description if available
    if tool.get('description'):
        return tool['description']
    
    return default_desc

def get_tool_icon(tool):
    """Get icon for a tool based on its category"""
    if not tool:
        return "puzzle-piece"
        
    return get_category_icon(tool.get('category', 'utility'))

def format_datetime(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """Format a timestamp to a human-readable date/time"""
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.datetime.fromtimestamp(timestamp)
        else:
            dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d")
        return dt.strftime(format_str)
    except (ValueError, TypeError):
        return timestamp

def get_version():
    """Get application version"""
    return "1.0.0"

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
        get_tool_icon=get_tool_icon,
        format_datetime=format_datetime,
        version=get_version(),
        now=lambda format_str="%Y": datetime.datetime.now().strftime(format_str),
        is_mobile=IS_MOBILE_DEVICE,
        debug=DEBUG,
        env=ENV
    )

# Export all settings as a dictionary
def get_settings():
    """Get all settings as a dictionary"""
    return {k: v for k, v in globals().items() 
            if not k.startswith('_') and k.isupper()}

# Load environment-specific settings
if ENV == 'production':
    try:
        from config_prod import *
    except ImportError:
        pass
elif ENV == 'test':
    try:
        from config_test import *
    except ImportError:
        pass
