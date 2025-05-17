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
import logging
from typing import Dict, List, Optional, Union, Any
import json

# Set up logger
logger = logging.getLogger(__name__)

class DocstringParser:
    """Class for parsing Python docstrings"""
    
    def __init__(self, file_path=None, content=None):
        """Initialize with either a file path or content"""
        self.file_path = file_path
        self.content = content
        self.docstring = None
        self.ast_tree = None
    
    def parse(self):
        """Parse the docstring and return structured information"""
        if not self.content and self.file_path:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.content = f.read()
            except Exception as e:
                logger.error(f"Error reading file {self.file_path}: {e}")
                return self._create_error_result(f"Error reading file: {str(e)}")
        
        if not self.content:
            return self._create_error_result("No content to parse")
        
        try:
            # Try to parse the file content as AST
            self.ast_tree = ast.parse(self.content)
            
            # Extract the module docstring
            self.docstring = ast.get_docstring(self.ast_tree)
            
            if not self.docstring:
                # Try to find a docstring in the first class or function
                for node in self.ast_tree.body:
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        class_docstring = ast.get_docstring(node)
                        if class_docstring:
                            self.docstring = class_docstring
                            break
            
            if not self.docstring:
                return self._create_empty_result()
            
            # Parse the docstring into sections
            doc_info = self._parse_docstring(self.docstring)
            
            # Find usage examples in the file
            examples = self._extract_usage_examples()
            if examples:
                doc_info["examples"] = examples
            
            # Find command-line parameters
            params = self._extract_parameters()
            if params:
                doc_info["parameters"] = params
            
            return doc_info
        
        except SyntaxError:
            # If AST parsing fails, try to extract docstring with regex
            logger.warning(f"AST parsing failed for {self.file_path}, trying regex fallback")
            return self._parse_with_regex()
        
        except Exception as e:
            logger.error(f"Error parsing docstring: {e}", exc_info=True)
            return self._create_error_result(f"Error parsing docstring: {str(e)}")
    
    def _create_error_result(self, error_message):
        """Create an error result dictionary"""
        return {
            "error": error_message,
            "raw": "",
            "title": os.path.basename(self.file_path) if self.file_path else "",
            "summary": "Error extracting documentation."
        }
    
    def _create_empty_result(self):
        """Create an empty result dictionary"""
        return {
            "raw": "",
            "title": os.path.basename(self.file_path) if self.file_path else "",
            "summary": "No documentation available.",
            "sections": {}
        }
    
    def _parse_with_regex(self):
        """Parse docstring using regex as a fallback"""
        try:
            # Look for triple-quoted docstring at the beginning of the file
            docstring_pattern = r'"""(.*?)"""'
            match = re.search(docstring_pattern, self.content, re.DOTALL)
            
            if match:
                self.docstring = match.group(1).strip()
                return self._parse_docstring(self.docstring)
            else:
                return self._create_empty_result()
        
        except Exception as e:
            logger.error(f"Error in regex parsing: {e}", exc_info=True)
            return self._create_error_result(f"Error in regex parsing: {str(e)}")
    
    def _parse_docstring(self, docstring):
        """
        Parse a docstring into structured sections.
        
        Args:
            docstring (str): The docstring to parse
            
        Returns:
            dict: A dictionary containing the parsed docstring information
        """
        if not docstring:
            return self._create_empty_result()
        
        # Clean up the docstring
        docstring = inspect.cleandoc(docstring)
        
        # Detect docstring format
        if self._is_pysnip_format(docstring):
            return self._parse_pysnip_format(docstring)
        elif self._is_google_format(docstring):
            return self._parse_google_format(docstring)
        elif self._is_numpy_format(docstring):
            return self._parse_numpy_format(docstring)
        else:
            # Default to simple format
            return self._parse_simple_format(docstring)
    
    def _is_pysnip_format(self, docstring):
        """Check if docstring is in PySnip format"""
        return "✒ Metadata" in docstring or "✒ Description" in docstring
    
    def _is_google_format(self, docstring):
        """Check if docstring is in Google format"""
        return re.search(r'\n\s*Args:', docstring) is not None
    
    def _is_numpy_format(self, docstring):
        """Check if docstring is in NumPy format"""
        return re.search(r'\n\s*Parameters\n\s*[-]+', docstring) is not None
    
    def _parse_pysnip_format(self, docstring):
        """Parse PySnip format docstring"""
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
    
    def _parse_google_format(self, docstring):
        """Parse Google format docstring"""
        # Extract the title (first line)
        lines = docstring.split('\n')
        title = lines[0].strip()
        
        # Extract the summary (paragraph before the first section)
        summary_lines = []
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if we've reached a section
            if re.match(r'^[A-Za-z]+:', line):
                break
            
            summary_lines.append(line)
            i += 1
        
        summary = ' '.join(summary_lines).strip()
        
        # Extract sections
        sections = {}
        current_section = None
        section_content = []
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if re.match(r'^[A-Za-z]+:', line):
                # New section found
                if current_section:
                    sections[current_section] = '\n'.join(section_content).strip()
                    section_content = []
                
                current_section = line.rstrip(':')
            elif current_section:
                section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        # Map to key sections
        key_sections = {
            "Description": summary,
            "Key Features": sections.get("Features", ""),
            "Usage Instructions": sections.get("Usage", "") or sections.get("Examples", ""),
            "Examples": sections.get("Examples", ""),
            "Command-Line Arguments": sections.get("Args", "") or sections.get("Arguments", ""),
            "Other Important Information": sections.get("Notes", "") or sections.get("Note", "")
        }
        
        return {
            "raw": docstring,
            "title": title,
            "summary": summary,
            "sections": sections,
            "key_sections": key_sections
        }
    
    def _parse_numpy_format(self, docstring):
        """Parse NumPy format docstring"""
        # Extract the title (first line)
        lines = docstring.split('\n')
        title = lines[0].strip()
        
        # Extract the summary (paragraph before the first section)
        summary_lines = []
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if we've reached a section
            if re.match(r'^[A-Za-z]+ *\n[-]+', '\n'.join(lines[i:i+2])):
                break
            
            summary_lines.append(line)
            i += 1
        
        summary = ' '.join(summary_lines).strip()
        
        # Extract sections
        sections = {}
        current_section = None
        section_content = []
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            # Check for section headers (followed by underline)
            if i < len(lines) and re.match(r'^[-]+$', lines[i].strip()):
                if current_section:
                    sections[current_section] = '\n'.join(section_content).strip()
                    section_content = []
                
                current_section = line
                i += 1  # Skip the underline
            elif current_section:
                section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        # Map to key sections
        key_sections = {
            "Description": summary,
            "Key Features": sections.get("Features", ""),
            "Usage Instructions": sections.get("Usage", "") or sections.get("Examples", ""),
            "Examples": sections.get("Examples", ""),
            "Command-Line Arguments": sections.get("Parameters", ""),
            "Other Important Information": sections.get("Notes", "") or sections.get("Note", "")
        }
        
        return {
            "raw": docstring,
            "title": title,
            "summary": summary,
            "sections": sections,
            "key_sections": key_sections
        }
    
    def _parse_simple_format(self, docstring):
        """Parse simple format docstring"""
        # Extract the title (first line)
        lines = docstring.split('\n')
        title = lines[0].strip()
        
        # Extract the summary (rest of the docstring)
        summary = '\n'.join(lines[1:]).strip()
        
        return {
            "raw": docstring,
            "title": title,
            "summary": summary,
            "sections": {},
            "key_sections": {
                "Description": summary,
                "Key Features": "",
                "Usage Instructions": "",
                "Examples": "",
                "Command-Line Arguments": "",
                "Other Important Information": ""
            }
        }
    
    def _extract_usage_examples(self):
        """
        Extract usage examples from file content.
        
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
            for match in re.finditer(pattern, self.content, re.DOTALL):
                example = match.group(1).strip()
                if example:
                    examples.append(example)
        
        # Look for doctest examples
        doctest_pattern = r'>>> (.*?)(?=\n\n|\n>>>|$)'
        for match in re.finditer(doctest_pattern, self.content, re.DOTALL):
            example = match.group(1).strip()
            if example:
                examples.append(example)
        
        # Look for examples in the docstring
        if self.docstring:
            examples_section = re.search(r'(?:Examples?|Usage):(.*?)(?=\n\n\w+:|\Z)', self.docstring, re.DOTALL)
            if examples_section:
                # Split by blank lines and process each example
                example_blocks = re.split(r'\n\s*\n', examples_section.group(1).strip())
                for block in example_blocks:
                    if block.strip():
                        examples.append(block.strip())
        
        return examples
    
    def _extract_parameters(self):
        """
        Extract command-line parameters from file content.
        
        Returns:
            list: A list of parameter dictionaries
        """
        parameters = []
        
        # Try AST-based extraction first
        if self.ast_tree:
            try:
                parameters = self._extract_parameters_ast()
            except Exception as e:
                logger.warning(f"AST parameter extraction failed: {e}")
        
        # Fall back to regex if needed
        if not parameters:
            parameters = self._extract_parameters_regex()
        
        return parameters
    
    def _extract_parameters_ast(self):
        """Extract parameters using AST parsing"""
        parameters = []
        
        for node in ast.walk(self.ast_tree):
            # Look for add_argument calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                if not node.args:
                    continue
                
                # Get parameter name from first argument
                arg_node = node.args[0]
                if isinstance(arg_node, ast.Str):
                    param_name = arg_node.s
                elif hasattr(ast, 'Constant') and isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, str):
                    param_name = arg_node.value
                else:
                    continue
                
                # Extract keyword arguments
                kwargs = {}
                for keyword in node.keywords:
                    if isinstance(keyword.value, ast.Str) or (hasattr(ast, 'Constant') and isinstance(keyword.value, ast.Constant)):
                        value = keyword.value.s if hasattr(keyword.value, 's') else keyword.value.value
                        kwargs[keyword.arg] = value
                    elif isinstance(keyword.value, ast.Name):
                        kwargs[keyword.arg] = keyword.value.id
                    elif isinstance(keyword.value, ast.List):
                        items = []
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Str) or (hasattr(ast, 'Constant') and isinstance(elt, ast.Constant)):
                                items.append(elt.s if hasattr(elt, 's') else elt.value)
                        kwargs[keyword.arg] = items
                
                # Create parameter info
                param_info = {
                    "name": param_name,
                    "clean_name": param_name.lstrip('-'),
                    "help": kwargs.get('help', ''),
                    "type": kwargs.get('type', 'str'),
                    "default": kwargs.get('default'),
                    "choices": kwargs.get('choices', []),
                    "required": kwargs.get('required', False)
                }
                
                parameters.append(param_info)
        
        return parameters
    
    def _extract_parameters_regex(self):
        """Extract parameters using regex"""
        parameters = []
        
        # Look for add_argument patterns
        arg_pattern = r'\.add_argument\([\'"](-{1,2}[a-zA-Z0-9_-]+)[\'"]'
        help_pattern = r'help=[\'"]([^\'"]+)[\'"]'
        type_pattern = r'type=([a-zA-Z0-9_\.]+)'
        default_pattern = r'default=([a-zA-Z0-9_\.\'"-]+)'
        required_pattern = r'required=(True|False)'
        choices_pattern = r'choices=\[([^\]]+)\]'
        
        for match in re.finditer(arg_pattern, self.content):
            param_name = match.group(1)
            
            # Find the help text in the surrounding context
            context = self.content[max(0, match.start() - 50):min(len(self.content), match.end() + 150)]
            help_match = re.search(help_pattern, context)
            help_text = help_match.group(1) if help_match else ""
            
            # Extract other parameter info
            type_match = re.search(type_pattern, context)
            param_type = type_match.group(1) if type_match else "str"
            
            default_match = re.search(default_pattern, context)
            default_value = default_match.group(1) if default_match else None
            
            required_match = re.search(required_pattern, context)
            required = required_match and required_match.group(1) == 'True'
            
            choices_match = re.search(choices_pattern, context)
            choices = choices_match.group(1).split(',') if choices_match else []
            
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

def extract_docstring(file_path):
    """
    Extract the docstring from a Python file.
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        dict: A dictionary containing the parsed docstring information
    """
    parser = DocstringParser(file_path=file_path)
    return parser.parse()

if __name__ == "__main__":
    # Test the docstring parser with a sample file
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        doc_info = extract_docstring(file_path)
        print(json.dumps(doc_info, indent=2))
    else:
        print("Usage: doc_parser.py <file_path>")
