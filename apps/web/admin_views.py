"""
Admin views for managing Django management commands.
"""

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .admin_commands import execute_command, get_all_commands, get_command_help


@staff_member_required
def admin_command_list(request):
    """
    Display a list of all available Django management commands.
    """
    commands_by_app = get_all_commands()

    # Count total commands
    total_commands = sum(len(cmds) for cmds in commands_by_app.values())

    context = {
        "commands_by_app": commands_by_app,
        "total_commands": total_commands,
        "page_title": "Admin Command Management",
        "active_tab": "admin_commands",
    }

    return render(request, "web/admin_commands.html", context)


@staff_member_required
@require_http_methods(["GET"])
def admin_command_detail(request, command_name):
    """
    Get detailed information about a specific command including its arguments.
    """
    command_info = get_command_help(command_name)

    if "error" in command_info:
        return JsonResponse({"error": command_info["error"]}, status=404)

    return JsonResponse(command_info)


@staff_member_required
@require_http_methods(["POST"])
def admin_command_execute(request):
    """
    Execute a Django management command and return the results.
    """
    try:
        data = json.loads(request.body)
        command_name = data.get("command")

        if not command_name:
            return JsonResponse({"error": "Command name is required"}, status=400)

        # Get arguments
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})

        # Convert kwargs values to appropriate types
        processed_kwargs = {}
        for key, value in kwargs.items():
            # Handle boolean flags
            if isinstance(value, str):
                if value.lower() in ("true", "1", "yes"):
                    processed_kwargs[key] = True
                elif value.lower() in ("false", "0", "no"):
                    processed_kwargs[key] = False
                else:
                    processed_kwargs[key] = value
            else:
                processed_kwargs[key] = value

        # Execute the command
        result = execute_command(command_name, args=args, kwargs=processed_kwargs)

        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
