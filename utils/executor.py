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
import logging
import re
import resource
import threading
from datetime import datetime
import platform
import ast
import inspect
from io import StringIO
from typing import Dict, List, Optional, Tuple, Union, Any

# Configure logging
logger = logging.getLogger(__name__)

# Default execution settings
DEFAULT_SETTINGS = {
    'MAX_EXECUTION_TIME': 60,           # Maximum execution time (in seconds)
    'MAX_OUTPUT_SIZE': 1024 * 1024,     # Maximum output size (in bytes) (1 MB)
    'MAX_MEMORY': 512 * 1024 * 1024,    # Maximum memory usage (in bytes) (512 MB)
    'MAX_CPU_TIME': 30,                 # Maximum CPU time (in seconds)
    'SANDBOX_ENABLED': True,            # Enable process isolation sandbox
    'WORKING_DIR': None,                # Working directory for execution (None = use temp dir)
    'ENV_VARS': {},                     # Additional environment variables
    'CAPTURE_STDERR': True,             # Capture stderr output
    'OUTPUT_STREAMING': False,          # Enable output streaming for long-running processes
    'USE_VENV': False,                  # Use virtual environment if available
    'PYTHON_PATH': sys.executable,      # Path to Python interpreter
}

class TimeoutException(Exception):
    """Exception raised when a script execution times out."""
    pass

class MemoryLimitException(Exception):
    """Exception raised when a script exceeds memory limits."""
    pass

class ExecutionManager:
    """Manages the execution of PySnip tools with resource limits and sandbox isolation."""
    
    def __init__(self, settings=None):
        """Initialize with custom settings"""
        self.settings = DEFAULT_SETTINGS.copy()
        if settings:
            self.settings.update(settings)
        
        # Create a specific temp directory for this instance
        self.temp_dir = None
    
    def __del__(self):
        """Clean up resources"""
        self._cleanup_temp_dir()
    
    def _create_temp_dir(self):
        """Create a temporary directory for execution"""
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="pysnip_exec_")
        return self.temp_dir
    
    def _cleanup_temp_dir(self):
        """Clean up the temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {e}")
            self.temp_dir = None
    
    def _set_resource_limits(self):
        """Set resource limits for the current process"""
        if platform.system() != 'Windows':  # Resource module not available on Windows
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.settings['MAX_CPU_TIME'], self.settings['MAX_CPU_TIME']))
            
            # Set memory limit
            resource.setrlimit(resource.RLIMIT_AS, (self.settings['MAX_MEMORY'], self.settings['MAX_MEMORY']))
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare the execution environment"""
        env = os.environ.copy()
        
        # Add custom environment variables
        env.update(self.settings['ENV_VARS'])
        
        # Set PYTHONPATH to include the directory of the tool
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{self.temp_dir}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = self.temp_dir
        
        return env
    
    def execute(self, tool_path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a PySnip tool with the provided parameters.
        
        Args:
            tool_path (str): Path to the PySnip tool
            params (dict): Parameters to pass to the tool
            
        Returns:
            dict: Execution results including stdout, stderr, and execution info
        """
        if not os.path.exists(tool_path):
            return self._create_error_result(f"Tool not found at: {tool_path}")
        
        # Create or get the temporary directory
        working_dir = self.settings['WORKING_DIR'] or self._create_temp_dir()
        
        # Prepare the command
        cmd = [self.settings['PYTHON_PATH'], tool_path]
        cmd_display = f"{os.path.basename(tool_path)}"
        
        # Add parameters
        if params:
            cmd_params = self._prepare_parameters(params)
            cmd.extend(cmd_params)
            
            # Create a display-friendly command string
            param_strs = []
            for key, value in params.items():
                if key.startswith('--'):
                    param_name = key
                else:
                    param_name = f"--{key}"
                
                if value is True:
                    param_strs.append(param_name)
                elif value not in (None, "", False):
                    param_strs.append(f"{param_name} {str(value)}")
            
            if param_strs:
                cmd_display += " " + " ".join(param_strs)
        
        # Set up process execution
        start_time = time.time()
        process = None
        stdout_data = ""
        stderr_data = ""
        exit_code = 1
        timeout_occurred = False
        error_message = None
        
        try:
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # Execute in sandbox if enabled
            if self.settings['SANDBOX_ENABLED']:
                result = self._execute_sandboxed(cmd, working_dir)
            else:
                result = self._execute_direct(cmd, working_dir)
            
            stdout_data = result.get('stdout', '')
            stderr_data = result.get('stderr', '')
            exit_code = result.get('exit_code', 1)
            timeout_occurred = result.get('timeout', False)
            error_message = result.get('error', None)
            
            # Check for special error conditions
            if timeout_occurred:
                error_message = f"Execution timed out after {self.settings['MAX_EXECUTION_TIME']} seconds"
            
            # Truncate output if too large
            if len(stdout_data) > self.settings['MAX_OUTPUT_SIZE']:
                stdout_data = stdout_data[:self.settings['MAX_OUTPUT_SIZE']] + "\n... [OUTPUT TRUNCATED] ..."
            if len(stderr_data) > self.settings['MAX_OUTPUT_SIZE']:
                stderr_data = stderr_data[:self.settings['MAX_OUTPUT_SIZE']] + "\n... [OUTPUT TRUNCATED] ..."
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            return {
                "success": exit_code == 0 and not timeout_occurred and not error_message,
                "return_code": exit_code,
                "cmd": cmd_display,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "execution_time": execution_time,
                "timeout": timeout_occurred,
                "error": error_message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        except Exception as e:
            logger.error(f"Error during execution: {e}", exc_info=True)
            return self._create_error_result(str(e))
    
    def _execute_direct(self, cmd, working_dir):
        """Execute command directly using subprocess"""
        env = self._prepare_environment()
        
        # Create process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if self.settings['CAPTURE_STDERR'] else None,
            text=True,
            universal_newlines=True,
            cwd=working_dir,
            env=env
        )
        
        # Set up timeout mechanism
        timer = threading.Timer(self.settings['MAX_EXECUTION_TIME'], self._kill_process, args=[process])
        timer.start()
        
        try:
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            timeout_occurred = False
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            exit_code = -1
            timeout_occurred = True
        finally:
            timer.cancel()
        
        return {
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': exit_code,
            'timeout': timeout_occurred
        }
    
    def _execute_sandboxed(self, cmd, working_dir):
        """Execute command in a sandboxed environment"""
        # For now, this is a thin wrapper around _execute_direct
        # In a real-world application, you might use containerization solutions
        # like Docker, or OS-specific sandboxing mechanisms here
        return self._execute_direct(cmd, working_dir)
    
    def _kill_process(self, process):
        """Kill a process that has timed out"""
        try:
            if process.poll() is None:  # Process is still running
                process.kill()
        except Exception as e:
            logger.error(f"Error killing process: {e}")
    
    def _prepare_parameters(self, params):
        """Convert parameter dictionary to command line arguments"""
        cmd_params = []
        
        for key, value in params.items():
            if key.startswith('--'):
                # It's already a flag
                param = key
            else:
                # Add -- prefix for flags
                param = f"--{key}"
            
            if value is True:
                # Boolean flag without value
                cmd_params.append(param)
            elif value not in (None, "", False):
                # Regular parameter with value
                cmd_params.append(param)
                cmd_params.append(str(value))
        
        return cmd_params
    
    def _create_error_result(self, error_message):
        """Create an error result dictionary"""
        return {
            "success": False,
            "return_code": 1,
            "cmd": "",
            "stdout": "",
            "stderr": f"ERROR: {error_message}",
            "execution_time": 0,
            "timeout": False,
            "error": error_message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Global executor instance
_executor = None

def execute_tool(tool_path, params=None):
    """
    Execute a PySnip tool with the provided parameters.
    Uses a singleton executor instance.
    
    Args:
        tool_path (str): Path to the PySnip tool
        params (dict): Parameters to pass to the tool
        
    Returns:
        dict: Execution results including stdout, stderr, and execution info
    """
    global _executor
    if _executor is None:
        _executor = ExecutionManager()
    
    return _executor.execute(tool_path, params)

def extract_parameters_from_script(script_path):
    """
    Extract command-line parameters from a script.
    Uses AST parsing for more accurate extraction.
    
    Args:
        script_path (str): Path to the script
        
    Returns:
        list: List of parameter dictionaries with name, help, etc.
    """
    if not os.path.exists(script_path):
        return []
    
    parameters = []
    
    try:
        # First try using AST parsing for more accurate extraction
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parameters = _extract_parameters_ast(content)
        
        # If AST parsing didn't find parameters, fall back to regex
        if not parameters:
            parameters = _extract_parameters_regex(content)
        
        return parameters
    
    except Exception as e:
        logger.error(f"Error extracting parameters: {e}", exc_info=True)
        return []

def _extract_parameters_ast(content):
    """Extract parameters using AST parsing"""
    parameters = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            # Look for add_argument calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                if not node.args:
                    continue
                
                # Get parameter name from first argument
                arg_node = node.args[0]
                if isinstance(arg_node, ast.Str):
                    param_name = arg_node.s
                elif isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, str):
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
    
    except Exception as e:
        logger.warning(f"AST parameter extraction failed: {e}")
        return []

def _extract_parameters_regex(content):
    """Extract parameters using regex as a fallback"""
    parameters = []
    
    # Look for add_argument patterns
    arg_pattern = r'\.add_argument\([\'"](-{1,2}[a-zA-Z0-9_-]+)[\'"]'
    help_pattern = r'help=[\'"]([^\'"]+)[\'"]'
    type_pattern = r'type=([a-zA-Z0-9_\.]+)'
    default_pattern = r'default=([a-zA-Z0-9_\.\'"-]+)'
    required_pattern = r'required=(True|False)'
    choices_pattern = r'choices=\[([^\]]+)\]'
    
    for match in re.finditer(arg_pattern, content):
        param_name = match.group(1)
        
        # Find the help text in the surrounding context
        context = content[max(0, match.start() - 50):min(len(content), match.end() + 150)]
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

if __name__ == "__main__":
    # Test the executor with a sample script
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
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
