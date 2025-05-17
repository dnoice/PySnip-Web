#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation Parser module for PySnip Web Interface
---------------------------------------------------
Extracts documentation from PySnip tools, including docstrings, 
usage examples, and parameter information.
"""

import os
import re
import ast
import inspect

def extract_docstring(file_path):
    """
    Extract the docstring from a Python file.
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        dict: A dictionary containing the parsed docstring information
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Parse the file content as AST
        module = ast.parse(file_content)
        
        # Extract the module docstring
        module_docstring = ast.get_docstring(module)
        
        if not module_docstring:
            return {
                "raw": "",
                "title": os.path.basename(file_path),
                "summary": "No documentation available.",
                "sections": {}
            }
        
        # Parse the docstring into sections
        doc_info = parse_docstring(module_docstring)
        
        # Find usage examples in the file
        examples = extract_usage_examples(file_content)
        if examples:
            doc_info["examples"] = examples
        
        # Find command-line parameters
        params = extract_parameters(file_content)
        if params:
            doc_info["parameters"] = params
        
        return doc_info
    
    except Exception as e:
        return {
            "error": f"Error extracting docstring: {str(e)}",
            "raw": "",
            "title": os.path.basename(file_path),
            "summary": "Error extracting documentation."
        }

def parse_docstring(docstring):
    """
    Parse a docstring into structured sections.
    
    Args:
        docstring (str): The docstring to parse
        
    Returns:
        dict: A dictionary containing the parsed docstring information
    """
    if not docstring:
        return {
            "raw": "",
            "title": "",
            "summary": "",
            "sections": {}
        }
    
    # Clean up the docstring
    docstring = inspect.cleandoc(docstring)
    
    # Extract the title (first line)
    lines = docstring.split('\n')
    title = lines[0].strip()
    
    # Extract the summary (paragraph after the title)
    summary_lines = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            break  # End of summary paragraph
        summary_lines.append(line)
    
    summary = ' '.join(summary_lines).strip()
    
    # Extract sections
    sections = {}
    current_section = None
    section_content = []
    
    for line in lines[len(summary_lines) + 1:]:
        if re.match(r'^[A-Za-z ]+:$', line.strip()) or re.match(r'^✒ [A-Za-z ]+:$', line.strip()):
            # New section found
            if current_section:
                sections[current_section] = '\n'.join(section_content).strip()
                section_content = []
            
            current_section = line.strip().rstrip(':').replace('✒ ', '')
        elif current_section:
            section_content.append(line)
    
    # Add the last section
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()
    
    # Look for PySnip specific sections
    key_sections = {
        "Description": sections.get("Description", ""),
        "Key Features": sections.get("Key Features", ""),
        "Usage Instructions": sections.get("Usage Instructions", ""),
        "Examples": sections.get("Examples", ""),
        "Command-Line Arguments": sections.get("Command-Line Arguments", ""),
        "Other Important Information": sections.get("Other Important Information", "")
    }
    
    return {
        "raw": docstring,
        "title": title,
        "summary": summary,
        "sections": sections,
        "key_sections": key_sections
    }

def extract_usage_examples(file_content):
    """
    Extract usage examples from file content.
    
    Args:
        file_content (str): The content of the Python file
        
    Returns:
        list: A list of usage examples found in the file
    """
    examples = []
    
    # Look for examples in comments or strings
    example_patterns = [
        r'# Example:[ \t]*(.*?)(?=\n\n|\n#|$)',
        r'# Usage:[ \t]*(.*?)(?=\n\n|\n#|$)',
        r'"""Example:[ \t]*(.*?)"""',
        r"'''Example:[ \t]*(.*?)'''"
    ]
    
    for pattern in example_patterns:
        for match in re.finditer(pattern, file_content, re.DOTALL):
            example = match.group(1).strip()
            if example:
                examples.append(example)
    
    # Look for doctest examples
    doctest_pattern = r'>>> (.*?)(?=\n\n|\n>>>|$)'
    for match in re.finditer(doctest_pattern, file_content, re.DOTALL):
        example = match.group(1).strip()
        if example:
            examples.append(example)
    
    return examples

def extract_parameters(file_content):
    """
    Extract command-line parameters from file content.
    
    Args:
        file_content (str): The content of the Python file
        
    Returns:
        list: A list of parameter dictionaries
    """
    parameters = []
    
    # Look for argparse parameter definitions
    # This is a simplistic approach and may not catch all parameters
    add_argument_pattern = r'\.add_argument\([\'"](-{1,2}[a-zA-Z0-9_-]+)[\'"](.*?)(?=\)\s*$|\),)'
    
    for match in re.finditer(add_argument_pattern, file_content, re.MULTILINE):
        param_name = match.group(1)
        param_args = match.group(2)
        
        # Extract parameter details
        help_match = re.search(r'help=[\'"]([^\'"]+)[\'"]', param_args)
        help_text = help_match.group(1) if help_match else ""
        
        type_match = re.search(r'type=([a-zA-Z0-9_\.]+)', param_args)
        param_type = type_match.group(1) if type_match else "str"
        
        default_match = re.search(r'default=([a-zA-Z0-9_\.\'"-]+)', param_args)
        default_value = default_match.group(1) if default_match else None
        
        choices_match = re.search(r'choices=\[([^\]]+)\]', param_args)
        choices = choices_match.group(1).split(',') if choices_match else None
        
        required_match = re.search(r'required=(True|False)', param_args)
        required = required_match and required_match.group(1) == 'True'
        
        parameters.append({
            "name": param_name,
            "clean_name": param_name.lstrip('-'),
            "help": help_text,
            "type": param_type,
            "default": default_value,
            "choices": choices,
            "required": required
        })
    
    return parameters

if __name__ == "__main__":
    # Test the docstring parser with a sample file
    import sys
    import json
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        doc_info = extract_docstring(file_path)
        print(json.dumps(doc_info, indent=2))
    else:
        print("Usage: doc_parser.py <file_path>")
