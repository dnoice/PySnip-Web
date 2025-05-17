#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executor module for PySnip Web Interface
---------------------------------------
Handles the execution of PySnip tools with provided parameters.
Captures output and handles execution in a safe manner.
"""

import os
import sys
import json
import subprocess
import shlex
import tempfile
import time
import signal
from datetime import datetime

# Maximum execution time (in seconds)
MAX_EXECUTION_TIME = 60

# Maximum output size (in bytes)
MAX_OUTPUT_SIZE = 1024 * 1024  # 1 MB

class TimeoutException(Exception):
    """Exception raised when a script execution times out."""
    pass

def execute_tool(tool_path, params=None):
    """
    Execute a PySnip tool with the provided parameters.
    
    Args:
        tool_path (str): Path to the PySnip tool
        params (dict): Parameters to pass to the tool
        
    Returns:
        dict: Execution results including stdout, stderr, and execution info
    """
    if not os.path.exists(tool_path):
        return {
            "success": False,
            "error": f"Tool not found at: {tool_path}",
            "stdout": "",
            "stderr": "",
            "execution_time": 0
        }
    
    # Prepare the command
    cmd = [sys.executable, tool_path]
    
    # Add parameters
    if params:
        for key, value in params.items():
            if key.startswith('--'):
                # It's already a flag
                param = key
            else:
                # Add -- prefix for flags
                param = f"--{key}"
            
            if value is True:
                # Boolean flag without value
                cmd.append(param)
            elif value not in (None, "", False):
                # Regular parameter with value
                cmd.append(param)
                cmd.append(str(value))
    
    # Set up process execution
    start_time = time.time()
    
    try:
        # Create a timeout function using SIGALRM
        def timeout_handler(signum, frame):
            raise TimeoutException("Script execution timed out")
        
        # Set the timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(MAX_EXECUTION_TIME)
        
        # Execute the command and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # Disable the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        
        # Truncate output if too large
        if len(stdout) > MAX_OUTPUT_SIZE:
            stdout = stdout[:MAX_OUTPUT_SIZE] + "\n... [OUTPUT TRUNCATED] ..."
        if len(stderr) > MAX_OUTPUT_SIZE:
            stderr = stderr[:MAX_OUTPUT_SIZE] + "\n... [OUTPUT TRUNCATED] ..."
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return {
            "success": process.returncode == 0,
            "return_code": process.returncode,
            "cmd": ' '.join(cmd),
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": execution_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except TimeoutException:
        return {
            "success": False,
            "error": f"Execution timed out after {MAX_EXECUTION_TIME} seconds",
            "cmd": ' '.join(cmd),
            "stdout": "",
            "stderr": f"ERROR: Script execution timed out after {MAX_EXECUTION_TIME} seconds",
            "execution_time": MAX_EXECUTION_TIME,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cmd": ' '.join(cmd),
            "stdout": "",
            "stderr": f"ERROR: {str(e)}",
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def extract_parameters_from_script(script_path):
    """
    Extract command-line parameters from a script.
    This is a basic implementation that just looks for argparse patterns.
    
    Args:
        script_path (str): Path to the script
        
    Returns:
        list: List of parameter dictionaries with name, help, etc.
    """
    if not os.path.exists(script_path):
        return []
    
    parameters = []
    
    # Read the script
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find potential argparse parameter definitions
    # This is a very basic implementation and may not catch all parameters
    # or may include false positives
    import re
    
    # Look for add_argument patterns
    arg_pattern = r'\.add_argument\([\'"](-{1,2}[a-zA-Z0-9_-]+)[\'"]'
    help_pattern = r'help=[\'"]([^\'"]+)[\'"]'
    
    for match in re.finditer(arg_pattern, content):
        param_name = match.group(1)
        
        # Find the help text in the surrounding context
        context = content[max(0, match.start() - 50):min(len(content), match.end() + 150)]
        help_match = re.search(help_pattern, context)
        help_text = help_match.group(1) if help_match else ""
        
        # Determine parameter type and default value
        type_match = re.search(r'type=([a-zA-Z0-9_]+)', context)
        param_type = type_match.group(1) if type_match else "str"
        
        default_match = re.search(r'default=([a-zA-Z0-9_\'"-]+)', context)
        default_value = default_match.group(1) if default_match else None
        
        parameters.append({
            "name": param_name,
            "clean_name": param_name.lstrip('-'),
            "help": help_text,
            "type": param_type,
            "default": default_value
        })
    
    return parameters

if __name__ == "__main__":
    # Test the executor with a sample script
    import sys
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        
        # Extract parameters
        print("Extracting parameters:")
        params = extract_parameters_from_script(script_path)
        for param in params:
            print(f"  {param['name']}: {param['help']}")
        
        # Execute the script
        print("\nExecuting script:")
        result = execute_tool(script_path)
        print(f"Success: {result['success']}")
        print(f"Execution time: {result['execution_time']:.2f} seconds")
        print("\nOutput:")
        print(result['stdout'])
        
        if result['stderr']:
            print("\nErrors:")
            print(result['stderr'])
    else:
        print("Usage: executor.py <script_path>")
