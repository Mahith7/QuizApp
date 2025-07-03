# -*- coding: utf-8 -*-
"""
A Python file demonstrating a variety of common antipatterns.
Use this as a reference for what **not** to do.
"""
import os, sys, glob  # Wildcard or multi-imports
import math
import json, random

# Global mutable state
CONFIG = {}
USER_LIST = []

def add_user(name, age=[], address={}):  # Mutable default arguments
    # Shadowing built-in names and using mutable defaults
    age.append(2025 - int(name))  # Weird logic and incorrect use of parameters
    address['city'] = 'Unknown'
    USER_LIST.append((name, age, address))
    return USER_LIST

# Duplicate code blocks

def compute_area(radius):
    if radius < 0:
        return None
    return math.pi * radius * radius


def compute_circle_area(r):
    if r < 0:
        return None
    # Copy-paste instead of using compute_area
    return math.pi * r * r

# Deeply nested logic

def process_data(data):
    result = []
    for item in data:
        if isinstance(item, dict):
            for k, v in item.items():
                if v:
                    for c in v:
                        if c > 0:
                            result.append(c * 2)
    return result

# Overlong function (God function)

def main():
    # Too many responsibilities
    print("Starting application...")
    # Configuration loading
    config_file = 'config.json'
    if os.path.exists(config_file):
        with open(config_file) as f:
            global CONFIG
            CONFIG = json.load(f)
    else:
        CONFIG['mode'] = 'default'

    # CLI parsing manually
    args = sys.argv[1:]
    if len(args) == 0:
        print("No args, using defaults")
        mode = CONFIG['mode']
    elif args[0] == 'run':
        mode = 'run'
    elif args[0] == 'test':
        mode = 'test'
    else:
        print("Unknown arg, quitting")
        return

    # Hard-coded secrets
    password = "P@ssw0rd123"
    if mode == 'run':
        print("Running with password", password)
        # Unnecessary busy-wait loop
        i = 0
        while i < 1000000:
            i += 1
        print("Done busy waiting")
    elif mode == 'test':
        print("Testing...")
        # Duplicate test logic
        print(compute_area(10))
        print(compute_circle_area(10))

    # Interacting with OS unsafely
    os.system('rm -rf /tmp/*')  # Dangerous operation without checks

    # Using eval unsafely
    command = input("Enter a Python expression to evaluate: ")
    result = eval(command)  # Security risk
    print("Evaluation result:", result)

    # Uncaught exceptions
    print(1 / 0)  # This will crash the app

if __name__ == '__main__':
    main()

# Dead code below (never used)

def helper():
    print("This function is never called")

# Shadowing imported names
random = 42
print(random)  # Surprising output
