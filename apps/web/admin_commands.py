"""
Admin command management utilities for discovering and executing Django management commands.
"""

import io
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.core.management import call_command, get_commands
from django.core.management.base import CommandError


def get_all_commands() -> Dict[str, List[str]]:
    """
    Discover all available Django management commands grouped by app.

    Returns:
        Dictionary mapping app names to lists of command names
    """
    commands = get_commands()
    grouped = defaultdict(list)

    for command_name, app_name in commands.items():
        grouped[app_name].append(command_name)

    # Sort commands within each app
    for app_name in grouped:
        grouped[app_name].sort()

    return dict(sorted(grouped.items()))


def get_command_help(command_name: str) -> Dict[str, Any]:
    """
    Get help information for a specific command.

    Args:
        command_name: Name of the management command

    Returns:
        Dictionary with command information including help text and arguments
    """
    try:
        # Get the command class
        commands = get_commands()
        if command_name not in commands:
            return {"error": f"Command '{command_name}' not found"}

        app_name = commands[command_name]

        # Import and instantiate the command to get its help
        from django.core.management import load_command_class

        command_class = load_command_class(app_name, command_name)
        command_instance = command_class()

        # Get help text
        help_text = command_instance.help or f"Execute {command_name}"

        # Get arguments
        arguments = []
        try:
            parser = command_instance.create_parser("manage.py", command_name)

            for action in parser._actions:
                # Skip help and version actions
                if action.dest in ("help", "version") or (
                    hasattr(action, "option_strings")
                    and any(opt in ("-h", "--help", "--version") for opt in action.option_strings)
                ):
                    continue

                arg_info = {
                    "name": action.dest,
                    "flags": list(action.option_strings)
                    if hasattr(action, "option_strings") and action.option_strings
                    else [f"--{action.dest}"],
                    "help": action.help or "",
                    "required": getattr(action, "required", False),
                }

                # Determine type
                if hasattr(action, "type") and action.type:
                    arg_info["type"] = str(action.type.__name__) if callable(action.type) else str(action.type)
                elif hasattr(action, "const") and action.const is not None:
                    # Boolean flag
                    arg_info["type"] = "bool"
                else:
                    arg_info["type"] = "str"

                # Handle positional arguments
                if hasattr(action, "nargs") and action.nargs:
                    arg_info["nargs"] = str(action.nargs)

                # Handle choices
                if hasattr(action, "choices") and action.choices:
                    try:
                        arg_info["choices"] = list(action.choices)
                    except (TypeError, ValueError):
                        pass

                # Handle default
                if hasattr(action, "default") and action.default is not None and action.default != "==SUPPRESS==":
                    arg_info["default"] = str(action.default)

                arguments.append(arg_info)
        except Exception:
            # If parsing fails, just return basic info
            pass

        return {
            "name": command_name,
            "app": app_name,
            "help": help_text,
            "arguments": arguments,
        }
    except Exception as e:
        return {"error": str(e)}


def execute_command(
    command_name: str,
    args: Optional[List[str]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    capture_output: bool = True,
) -> Dict[str, Any]:
    """
    Execute a Django management command and capture its output.

    Args:
        command_name: Name of the management command to execute
        args: Positional arguments for the command
        kwargs: Keyword arguments for the command
        capture_output: Whether to capture stdout/stderr

    Returns:
        Dictionary with execution results including output, errors, and exit code
    """
    args = args or []
    kwargs = kwargs or {}

    result = {
        "command": command_name,
        "args": args,
        "kwargs": kwargs,
        "success": False,
        "output": "",
        "error": "",
        "exit_code": 0,
    }

    old_stdout = None
    old_stderr = None
    stdout_capture = None
    stderr_capture = None

    try:
        if capture_output:
            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

        try:
            # Execute the command
            call_command(command_name, *args, **kwargs, verbosity=2)
            result["success"] = True
            result["exit_code"] = 0
        except CommandError as e:
            result["error"] = str(e)
            result["exit_code"] = 1
        except SystemExit as e:
            result["exit_code"] = e.code if e.code is not None else 1
            if not result["error"]:
                result["error"] = f"Command exited with code {result['exit_code']}"
        except Exception as e:
            result["error"] = str(e)
            result["exit_code"] = 1

        if capture_output and stdout_capture:
            result["output"] = stdout_capture.getvalue()
            if stderr_capture:
                error_output = stderr_capture.getvalue()
                if error_output:
                    result["error"] = (result["error"] + "\n" + error_output).strip()
    except Exception as e:
        result["error"] = f"Failed to execute command: {str(e)}"
        result["exit_code"] = 1
    finally:
        if capture_output:
            # Restore stdout/stderr
            if old_stdout:
                sys.stdout = old_stdout
            if old_stderr:
                sys.stderr = old_stderr

    return result
