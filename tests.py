import os
import inspect
import pytest

# Path to your library and tests directory
library_path = "eegrasp"
tests_path = "eegrasp/tests"

# Ensure the tests directory exists
os.makedirs(tests_path, exist_ok=True)

# Get a list of Python modules in your library (excluding __init__.py)
modules = [f for f in os.listdir(library_path) if f.endswith('.py') and f != '__init__.py']

# Template for test files
test_template = """import pytest
from eegrasp.{module_name} import *

{test_functions}
"""

test_function_template = """
def test_{func_name}():
    # Test inputs based on function parameters
    # TODO: Replace with meaningful values
    inputs = {inputs}
    expected_output = {expected_output}
    assert {func_name}(*inputs) == expected_output
"""

def generate_inputs_and_expected_output(func):
    """
    Generate example inputs and expected output based on function's signature.
    This is a basic implementation; customize it for specific cases.
    """
    signature = inspect.signature(func)
    parameters = signature.parameters

    inputs = []
    expected_output = None

    # Example inputs based on parameter types (basic types)
    for name, param in parameters.items():
        if param.annotation is int:
            inputs.append(0)  # Example integer input
        elif param.annotation is float:
            inputs.append(0.0)  # Example float input
        elif param.annotation is str:
            inputs.append("")  # Example string input
        elif param.annotation is list:
            inputs.append([])  # Example empty list
        else:
            inputs.append(None)  # Default input for other types

    # A placeholder expected output; customize this logic based on function
    if func.__name__ == "add":  # Example for a function named 'add'
        expected_output = sum(inputs)
    elif func.__name__ == "subtract":  # Example for a function named 'subtract'
        expected_output = inputs[0] - inputs[1]
    else:
        expected_output = None  # Default if not specifically handled

    return inputs, expected_output

# Generate test files
for module in modules:
    module_name = module.replace('.py', '')
    test_file = f"test_{module_name}.py"
    test_file_path = os.path.join(tests_path, test_file)

    # Dynamically import the module
    module_obj = __import__(f"eegrasp.{module_name}", fromlist=[module_name])

    # Get all functions and methods
    test_functions = ""
    for name, obj in inspect.getmembers(module_obj):
        if inspect.isfunction(obj):
            inputs, expected_output = generate_inputs_and_expected_output(obj)
            test_functions += test_function_template.format(func_name=name, inputs=inputs, expected_output=expected_output)
        elif inspect.isclass(obj):
            # For classes, add tests for their methods
            for class_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                inputs, expected_output = generate_inputs_and_expected_output(method)
                test_functions += test_function_template.format(func_name=f"{name}_{class_name}", inputs=inputs, expected_output=expected_output)

    # Create the test file with the template
    with open(test_file_path, 'w') as f:
        f.write(test_template.format(module_name=module_name, test_functions=test_functions))

print("Test files created successfully!")
