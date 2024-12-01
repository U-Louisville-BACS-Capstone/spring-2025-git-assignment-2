#!/usr/bin/env python3

import os
import sys
import logging
import textwrap
import subprocess
import importlib.util

# Check a Python script and see if a specific function is defined.  As
# expected, this will fail if the Python script itself fails to parse
# or evaluate.
def check_for_function(path, function_name):
    logging.info(f"Checking whether function {function_name} is in {path}")

    # Extract the module name from the file path
    parts = os.path.splitext(os.path.basename(path))
    module_name = parts[0]

    # Load the module dynamically
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None:
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    except Exception as e:
        # If we get an exception, it's likely that the script itself
        # didn't parse (e.g., it had a syntax error).
        logging.error(f"Error loading {path}: {e}")
        return False

    # Check if the function exists in the module
    found = hasattr(module, function_name)
    logging.info(f"--> {found}")
    return found

#----------------

# Minor optimization: only read a given file once
_file_string_cache = dict()

# Look for a specific string in a file
def check_for_string(path, string):
    logging.info(f"Checking whether string \"{string}\" is in {path}")

    if path in _file_string_cache:
        content = _file_string_cache[path]
    else:
        with open(path) as fp:
            content = fp.read()
        _file_string_cache[path] = content

    found = string in content
    logging.info(f"--> {found}")
    return found

#----------------

# Sentinel value
ITERATION = '{i}'

# Run a command and see if it emits the expected output
def check_run(expected_results_file, count=1, args=[]):
    outputs = list()
    for i in range(count):
        cmd = ['python3', './calculator.py']
        for arg in args:
            if arg == ITERATION:
                cmd.append('--seed')
                cmd.append(str(i+1))
            else:
                cmd.append(arg)

        cmd_pp = ' '.join(cmd)
        logging.info(f"Running test iteration {i+1}: {cmd_pp}")
        rc = subprocess.run(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)

        if rc.returncode != 0:
            logging.error(f"Command returned non-zero exit status (rc.returncode): {cmd_pp}")
            exit(1)

        output = rc.stdout.decode('utf-8')
        if output:
            outputs.append(output.strip())

    actual_output = '\n'.join(outputs).strip()

    with open(expected_results_file) as fp:
        expected_output = fp.read().strip()
    if expected_output != actual_output:
        logging.error(f"Command returned unexpected output: {cmd_pp}")
        logging.error("Expected ouput\n" +
                      textwrap.indent(expected_output, "    "))
        logging.error(f"Actual output:\n" +
                      textwrap.indent(actual_output, "    "))
        logging.error("Test failure")
        exit(1)

#----------------

def main():
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='%(levelname)s: %(message)s')

    # Check what functionality the calculator has
    source = "calculator.py"

    have_original = \
        check_for_function(source, "add") and \
        check_for_function(source, "subtract") and \
        check_for_function(source, "main")

    have_divmul = \
        check_for_function(source, "divide") and \
        check_for_function(source, "multiply")

    have_addsub = \
        check_for_string(source, "Adding then subtracting!") and \
        check_for_string(source, "Subtracting then adding!")

    have_logging = \
        check_for_string(source, "import logging") and \
        check_for_string(source, "logging.basicConfig")

    have_debug = \
        check_for_string(source, "import argparse") and \
        check_for_string(source, "--debug")

    have_seed = \
        check_for_string(source, "import argparse") and \
        check_for_string(source, "--seed")

    # Convert the above booleans into an aggregated value for
    # simplicity of checking, below.
    case = \
         int(have_original) * 1  + \
         int(have_divmul)   * 2  + \
         int(have_addsub)   * 4  + \
         int(have_logging)  * 8  + \
         int(have_debug)    * 16 + \
         int(have_seed)     * 32
    logging.info(f"Testing case: {case}")

    #----------------

    # Decide how to run the calculator and which output to text against,
    # based on what we found above.
    #
    # Over the course of this assignment, there are finite
    # possibilities that we care about (i.e., need to be able to check
    # for correctness).

    def _run_multiple(base, seed):
        check_run(f'{base}.txt')
        check_run(f'{base}-debug.txt', args=['--debug'])
        if seed:
            check_run(f'{base}-seeds.txt',  args=['--debug', ITERATION],
                      count=100)

    base = 'tests/expected-results'
    if case == 1:
        check_run(f'{base}-1-original.txt')

    elif case == 3:
        check_run(f'{base}-3-divmul.txt')

    elif case == 5:
        check_run(f'{base}-5-addsub.txt')

    elif case == 9:
        check_run(f'{base}-9-logging.txt')

    elif case == 25:
        base += '-25-logging'
        _run_multiple(base, seed=False)

    elif case == 57:
        base += '-57-seed'
        _run_multiple(base, seed=True)

    elif case == 59:
        base += '-59-divmul'
        _run_multiple(base, seed=True)

    elif case == 61:
        base += '-61-addsub'
        _run_multiple(base, seed=True)

    elif case == 63:
        base += '-63-all'
        _run_multiple(base, seed=True)

    else:
        # If we got here, the calculator is either non-functional
        # (e.g., syntax error) or it does not have one of the valid
        # sets of functionality that we know how to test.
        logging.error("Did not find a valid testing scenario -- fail")
        exit(1)

    # If we got here, everything passed.  Yay!
    logging.info("SUCCESS!")

main()
