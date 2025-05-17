#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySnip Web Interface - Enhanced Version
-------------------
A web-based catalog and execution interface for the PySnip tool collection.
"""

from flask import Flask, render_template, request, jsonify, abort, send_from_directory, session, g
import os
import sys
import json
import subprocess
import shlex
import logging
from datetime import datetime
from functools import wraps
import time
import werkzeug.exceptions

# Import utility modules
from utils.scanner import scan_pysnip_directory, get_tool_details, get_category_details, get_related_tools
from utils.executor import execute_tool, extract_parameters_from_script
from utils.doc_parser import extract_docstring

# Configuration
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app.config.get('LOG_FILE', 'pysnip_explorer.log')),
        logging.StreamHandler()
    ]
)

# Global variables
PYSNIP_ROOT = app.config['PYSNIP_ROOT']
CATALOG = None  # Will be populated by scanning the directory
LAST_SCAN_TIME = 0
SCAN_INTERVAL = app.config.get('CATALOG_SCAN_INTERVAL', 3600)  # Rescan interval in seconds

# Cache decorator
def cached(timeout=300):
    def decorator(f):
        cache = {}
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            if key in cache and now - cache[key]['time'] < timeout:
                return cache[key]['value']
            result = f(*args, **kwargs)
            cache[key] = {'value': result, 'time': now}
            return result
        return decorated_function
    return decorator

# Rate limiting decorator
def rate_limit(limit=5, per=60):
    def decorator(f):
        rates = {}
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.remote_addr
            now = time.time()
            if key not in rates:
                rates[key] = []
            # Clean up old requests
            rates[key] = [t for t in rates[key] if now - t < per]
            # Check if rate limit exceeded
            if len(rates[key]) >= limit:
                app.logger.warning(f"Rate limit exceeded for {key}")
                return jsonify({"error": "Rate limit exceeded"}), 429
            # Add this request
            rates[key].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize or refresh the catalog
def initialize_catalog():
    global CATALOG, LAST_SCAN_TIME
    try:
        CATALOG = scan_pysnip_directory(PYSNIP_ROOT)
        LAST_SCAN_TIME = time.time()
        app.logger.info(f"Catalog initialized with {len(CATALOG['categories'])} categories")
        return CATALOG
    except Exception as e:
        app.logger.error(f"Error initializing catalog: {e}")
        if CATALOG is None:
            CATALOG = {
                "name": "PySnip Collection",
                "description": "Error loading PySnip catalog",
                "categories": [],
                "tools_count": 0,
                "root_path": PYSNIP_ROOT,
                "error": str(e)
            }
        return CATALOG

# Check if catalog needs refreshing
@app.before_request
def check_catalog():
    global CATALOG, LAST_SCAN_TIME
    # Initialize catalog if it doesn't exist
    if CATALOG is None:
        initialize_catalog()
    # Check if it's time to refresh the catalog
    elif time.time() - LAST_SCAN_TIME > SCAN_INTERVAL:
        app.logger.info("Refreshing catalog...")
        initialize_catalog()

# Initialize catalog on startup
with app.app_context():
    initialize_catalog()

# Add template context processor
@app.context_processor
def inject_template_globals():
    """Inject global variables into templates"""
    from config import inject_template_globals
    return inject_template_globals()

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', catalog=CATALOG), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal server error: {e}")
    return render_template('500.html', error=str(e), catalog=CATALOG), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, werkzeug.exceptions.HTTPException):
        return e
    
    # Log the error
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    
    # Return a custom error response
    return render_template('500.html', error=str(e), catalog=CATALOG), 500

# Routes
@app.route('/')
def index():
    """Home page - show categories"""
    return render_template('index.html', catalog=CATALOG)

@app.route('/category/<category_name>')
def category(category_name):
    """Show tools in a specific category"""
    category_info = get_category_details(CATALOG, category_name)
    if not category_info:
        abort(404)
    return render_template('category.html', category=category_info)

@app.route('/mobile')
def mobile():
    """Mobile-friendly version of the home page"""
    return render_template('mobile.html', catalog=CATALOG)

@app.route('/tool/<path:tool_path>')
def tool(tool_path):
    """Show details and interface for a specific tool"""
    tool_info = get_tool_details(CATALOG, tool_path)
    if not tool_info:
        abort(404)
    
    return render_template('tool.html', tool=tool_info)

@app.route('/execute', methods=['POST'])
@rate_limit(limit=10, per=60)  # Limit to 10 executions per minute
def execute():
    """Execute a tool with provided parameters"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    tool_path = data.get('tool_path')
    params = data.get('params', {})
    
    if not tool_path:
        return jsonify({"error": "Tool path is required"}), 400
    
    # Validate tool path
    full_path = os.path.join(PYSNIP_ROOT, tool_path)
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({"error": "Tool not found"}), 404
    
    # Check if tool execution is enabled
    if not app.config.get('ENABLE_EXECUTIONS', True):
        return jsonify({"error": "Tool execution is disabled"}), 403
    
    # Check for prohibited commands
    prohibited_commands = app.config.get('PROHIBITED_COMMANDS', [])
    for param_name, param_value in params.items():
        if isinstance(param_value, str):
            for cmd in prohibited_commands:
                if cmd in param_value:
                    app.logger.warning(f"Prohibited command detected: {cmd} in {param_value}")
                    return jsonify({"error": "Prohibited command detected"}), 403
    
    # Execute the tool and capture output
    app.logger.info(f"Executing tool: {tool_path} with params: {params}")
    try:
        result = execute_tool(full_path, params)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error executing tool: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": f"ERROR: {str(e)}",
            "execution_time": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/parameters/<path:tool_path>')
@cached(timeout=300)  # Cache for 5 minutes
def get_parameters(tool_path):
    """Get parameters for a tool"""
    full_path = os.path.join(PYSNIP_ROOT, tool_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "Tool not found"}), 404
    
    try:
        parameters = extract_parameters_from_script(full_path)
        return jsonify({"parameters": parameters})
    except Exception as e:
        app.logger.error(f"Error extracting parameters: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/docs/<path:tool_path>')
@cached(timeout=300)  # Cache for 5 minutes
def docs(tool_path):
    """Get documentation for a tool"""
    full_path = os.path.join(PYSNIP_ROOT, tool_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "Tool not found"}), 404
    
    try:
        docstring = extract_docstring(full_path)
        return jsonify(docstring)
    except Exception as e:
        app.logger.error(f"Error extracting docstring: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/source/<path:tool_path>')
@cached(timeout=300)  # Cache for 5 minutes
def source(tool_path):
    """Get source code for a tool"""
    full_path = os.path.join(PYSNIP_ROOT, tool_path)
    if not os.path.exists(full_path):
        return jsonify({"error": "Tool not found"}), 404
    
    # Check if source view is enabled
    if not app.config.get('ENABLE_SOURCE_VIEW', True):
        return jsonify({"error": "Source view is disabled"}), 403
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        return jsonify({"source": source_code})
    except Exception as e:
        app.logger.error(f"Error reading source code: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/related/<category_name>')
@cached(timeout=600)  # Cache for 10 minutes
def related(category_name):
    """Get related tools for a category"""
    try:
        related_tools = get_related_tools(CATALOG, category_name)
        return jsonify({"tools": related_tools})
    except Exception as e:
        app.logger.error(f"Error getting related tools: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/random')
def random_tool():
    """Get a random tool"""
    import random
    if not CATALOG or not CATALOG.get('categories'):
        return redirect('/')
    
    categories = CATALOG['categories']
    # Choose a random category with tools
    valid_categories = [c for c in categories if c['tools']]
    if not valid_categories:
        return redirect('/')
    
    category = random.choice(valid_categories)
    tool = random.choice(category['tools'])
    
    return redirect(f"/tool/{tool['relative_path']}")

@app.route('/search')
def search():
    """Search for tools"""
    query = request.args.get('q', '').lower()
    if not query:
        return redirect('/')
    
    results = []
    
    for category in CATALOG.get('categories', []):
        for tool in category.get('tools', []):
            tool_name = tool.get('name', '').lower()
            if query in tool_name:
                results.append(tool)
    
    return render_template('search.html', query=query, results=results, catalog=CATALOG)

@app.route('/static/images/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.config['CUSTOM_STATIC_PATH'], filename)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "tools_count": CATALOG.get('tools_count', 0) if CATALOG else 0,
        "categories_count": len(CATALOG.get('categories', [])) if CATALOG else 0,
        "uptime": time.time() - LAST_SCAN_TIME if LAST_SCAN_TIME else 0
    })

if __name__ == '__main__':
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    app.run(host=host, port=port, debug=debug)
