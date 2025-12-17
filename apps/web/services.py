"""
Services for web app functionality
"""

import json
import math
from typing import Any, Dict

import numpy as np
from scipy import stats
from scipy.special import beta, erf, erfc, gamma


class EquationCalculator:
    """Service for calculating equation results"""

    def calculate(self, equation, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate equation result with given parameters.

        Returns:
            {
                'result': float or dict,
                'formatted_result': str,
                'error': str or None
            }
        """
        try:
            # Parse parameters and convert to appropriate types
            parsed_params = self._parse_parameters(equation, parameters)

            # Execute calculation based on implementation type
            if equation.implementation_type == "python":
                result = self._execute_python(equation, parsed_params)
            elif equation.implementation_type == "javascript":
                # For now, we'll use Python for JS equations too
                # In production, you might want to use a JS runtime
                result = self._execute_python(equation, parsed_params)
            else:
                # Formula-based calculation
                result = self._execute_formula(equation, parsed_params)

            return {
                "result": result,
                "formatted_result": self._format_result(result),
                "error": None,
            }
        except Exception as e:
            return {
                "result": None,
                "formatted_result": "",
                "error": str(e),
            }

    def generate_graph(self, equation, parameters: Dict[str, Any], graph_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate graph data for an equation.

        Returns:
            {
                'x': List[float],
                'y': List[float],
                'x_label': str,
                'y_label': str,
                'title': str,
            }
        """
        try:
            # Get graph configuration from equation or provided config
            config = equation.graph_config_json.copy()
            config.update(graph_config)

            # Generate data points
            x_min = float(config.get("x_min", 0))
            x_max = float(config.get("x_max", 10))
            num_points = int(config.get("num_points", 100))

            x_values = np.linspace(x_min, x_max, num_points)
            y_values = []

            # Create a copy of parameters for each x value
            for x in x_values:
                params = parameters.copy()
                # Set x variable (usually 'x' or from config)
                x_var = config.get("x_variable", "x")
                params[x_var] = float(x)

                # Calculate y value
                parsed_params = self._parse_parameters(equation, params)
                if equation.implementation_type == "python":
                    y = self._execute_python(equation, parsed_params)
                else:
                    y = self._execute_formula(equation, parsed_params)

                y_values.append(float(y) if isinstance(y, (int, float)) else 0.0)

            return {
                "x": x_values.tolist(),
                "y": y_values,
                "x_label": config.get("x_label", "x"),
                "y_label": config.get("y_label", "f(x)"),
                "title": config.get("title", equation.name),
            }
        except Exception as e:
            return {
                "x": [],
                "y": [],
                "error": str(e),
            }

    def _parse_parameters(self, equation, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate parameters according to equation variable definitions"""
        parsed = {}

        # Get variable definitions
        variables = {v.name: v for v in equation.variables.all()}

        # Also check parameters_json for fallback
        params_def = equation.parameters_json or {}

        for key, value in parameters.items():
            # Get variable definition
            var_def = variables.get(key) or params_def.get(key, {})

            # Convert value based on type
            if isinstance(var_def, dict):
                var_type = var_def.get("type", "float")
            else:
                var_type = var_def.variable_type if hasattr(var_def, "variable_type") else "float"

            try:
                if var_type == "integer":
                    parsed[key] = int(float(value))
                elif var_type == "float":
                    parsed[key] = float(value)
                elif var_type == "boolean":
                    parsed[key] = bool(value)
                else:
                    parsed[key] = value
            except (ValueError, TypeError):
                # Use default if conversion fails
                if isinstance(var_def, dict):
                    default = var_def.get("default", 0)
                else:
                    default = var_def.default_value if hasattr(var_def, "default_value") else 0
                parsed[key] = default
        return parsed

    def _execute_python(self, equation, parameters: Dict[str, Any]) -> Any:
        """Execute Python implementation"""
        if not equation.implementation_code:
            raise ValueError("No implementation code provided")

        # Handle lambda parameter name conflict (Python keyword)
        # Replace 'lambda' key with 'lambda_param' if present
        safe_parameters = {}
        for key, value in parameters.items():
            if key == "lambda":
                safe_parameters["lambda_param"] = value
            else:
                safe_parameters[key] = value

        # Create safe execution environment
        safe_dict = {
            "math": math,
            "np": np,
            "numpy": np,
            "stats": stats,
            "gamma": gamma,
            "beta": beta,
            "erf": erf,
            "erfc": erfc,
            "pi": math.pi,
            "e": math.e,
            **safe_parameters,
        }

        # Execute code
        exec(equation.implementation_code, {"__builtins__": {}}, safe_dict)

        # Return result (assuming code sets 'result' variable)
        if "result" in safe_dict:
            return safe_dict["result"]
        elif "y" in safe_dict:
            return safe_dict["y"]
        else:
            raise ValueError("Implementation code must set 'result' or 'y' variable")

    def _execute_formula(self, equation, parameters: Dict[str, Any]) -> Any:
        """Execute formula-based calculation"""
        # For formula-based equations, we'll need to parse the formula
        # This is a simplified version - in production you'd use a proper formula parser
        formula = equation.formula_text

        # Replace parameter names with values
        for key, value in parameters.items():
            formula = formula.replace(key, str(value))

        # Evaluate (in production, use a safer evaluator)
        try:
            return eval(formula, {"__builtins__": {}}, {"math": math, "np": np, "pi": math.pi, "e": math.e})
        except Exception:
            # Fallback to Python implementation if available
            if equation.implementation_code:
                return self._execute_python(equation, parameters)
            raise ValueError("Could not evaluate formula")

    def _format_result(self, result: Any) -> str:
        """Format result for display"""
        if isinstance(result, (int, float)):
            if abs(result) < 0.001 or abs(result) > 1e6:
                return f"{result:.6e}"
            else:
                return f"{result:.6f}"
        elif isinstance(result, (list, tuple)):
            return f"[{', '.join(self._format_result(r) for r in result)}]"
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return str(result)
