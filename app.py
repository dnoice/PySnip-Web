#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySnip Web Interface
-------------------
A web-based catalog and execution interface for the PySnip tool collection.
"""

from flask import Flask, render_template, request, jsonify, abort, send_from_directory
import os
import sys
import json
import subprocess
import shlex
from datetime import datetime

# Import utility modules
from utils.scanner import scan_pysnip_directory, get_tool_details, get_category_details
from utils.executor import execute_tool
from utils.doc_parser import extract_docstring

# Configuration
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Global variables
PYSNIP_ROOT = app.config['PYSNIP_ROOT']
CATALOG = None  # Will be populated by scanning the directory

# Initialize the catalog on startup
@app.before_first_request
def initialize_catalog():
    global CATALOG
    CATALOG = scan_pysnip_directory(PYSNIP_ROOT)
    app.logger.info(f"Catalog initialized with {len(CATALOG['categories'])} categories")

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

@app.route('/tool/<path:tool_path>')
def tool(tool_path):
    """Show details and interface for a specific tool"""
    tool_info = get_tool_details(CATALOG, tool_path)
    if not tool_info:
        abort(404)
    
    # Extract additional info like docstring
    docstring = extract_docstring(os.path.join(PYSNIP_ROOT, tool_path))
    tool_info['docstring'] = docstring
    
    return render_template('tool.html', tool=tool_info)

@app.route('/execute', methods=['POST'])
def execute():
    """Execute a tool with provided parameters"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    tool_path = data.get('tool_path')
    params = data.get('params', {})
    
    if not tool_path:
        return jsonify({"error": "Tool path is required"}), 400
    
    # Execute the tool and capture output
    result = execute_tool(os.path.join(PYSNIP_ROOT, tool_path), params)
    return jsonify(result)

@app.route('/docs/<path:tool_path>')
def docs(tool_path):
    """Get documentation for a tool"""
    full_path = os.path.join(PYSNIP_ROOT, tool_path)
    if not os.path.exists(full_path):
        abort(404)
    
    docstring = extract_docstring(full_path)
    return jsonify({"docstring": docstring})

@app.route('/static/images/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.config['CUSTOM_STATIC_PATH'], filename)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
