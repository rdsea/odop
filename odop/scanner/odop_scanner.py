"""
Simple scanner given by Linh Truong based on previous training examples for
dealing with decorator.

The scanner is written based on basic code/example of traversing the AST using
python library for teaching purpose.
"""

import argparse
import ast

from loguru import logger

# odop decorators, provide a list of decorators we have, add them into the list
ODOP_DECORATORS = ["odop_task", "task_manager", "task_manager.odop_task"]
# example of odop specific functions, we can have some specific functions that
# we want to scan
ODOP_PREDEFINED_FUNCTIONS = ["__odopcall__", "__odopprocess__"]


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_file", help="source file")
    args = parser.parse_args()
    source_file = args.source_file
    # FIXME: we may need to check provided symbols and used libraries, e.g., using invectio
    with open(source_file, encoding="utf-8") as fp:
        source_code = fp.read()
        source_ast = ast.parse(source_code)
    # follow the basic way of walking through the AST
    for node in ast.walk(source_ast):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
            # check if it is a specific ODOP function
            if node.name in ODOP_PREDEFINED_FUNCTIONS:
                print("------------------")
                print("Detected ODOP related code, extracting ...")
                print(
                    f"Nodetype: {type(node).__name__}, odop-predefined function ={node.name}"
                )
                print("Function source code")
                print(ast.unparse(node))
                print("Now you can manage the extracted code ...")
            else:
                for decorator in node.decorator_list:
                    decorator_module = None
                    decorator_name = None
                    is_attribute = False
                    if isinstance(decorator, ast.Call):
                        logger.debug("Decorator as a Call")
                        if isinstance(decorator.func, ast.Name):
                            logger.debug("Decorator function is Name")
                            decorator_name = decorator.func.id
                        elif isinstance(decorator.func, ast.Attribute):
                            logger.debug("Decorator function is Attribute")
                            decorator_name = decorator.func.attr
                            decorator_module = decorator.func.value.id
                    elif isinstance(decorator, ast.Name):
                        logger.debug("Decorator  is Name")
                        decorator_name = decorator.id
                    elif isinstance(decorator, ast.Attribute):
                        logger.debug("Decorator  is Attribute")
                        decorator_name = decorator.attr
                        is_attribute = True
                    else:
                        logger.debug("Unknown/skip situation")
                        decorator_name = None
                    # for a decorato args and keywords:
                    # @decorator(args, keyword=value)
                    if not is_attribute:
                        decorator_args = [ast.dump(arg) for arg in decorator.args]
                        # value of a keyword is an expr, so we just dump it, if we assume
                        # it is a constant then we can get the value
                        # provide it as key=value
                        decorator_keywords = [
                            {"key": keyword.arg, "value": ast.dump(keyword.value)}
                            for keyword in decorator.keywords
                        ]
                    logger.debug(
                        f"Find decorator name: {decorator_name} and decorator module: {decorator_module}"
                    )
                    # just make a simple check, if name or module is in the list
                    if (decorator_name in ODOP_DECORATORS) or (
                        decorator_module in ODOP_DECORATORS
                    ):
                        print("------------------")
                        print("Detected ODOP related code, extracting ...")
                        print(
                            f"Nodetype: {type(node).__name__}, decorator name: {decorator_name}, decorator module: {decorator_module}"
                        )
                        if not is_attribute:
                            print(f"Decorators args: \n{decorator_args}")
                            print(f"Decorators keywords:\n{decorator_keywords}")
                        # we can travel the node and get function calls
                        print(" === Function source code ===")
                        print(ast.unparse(node))
                        print("Now you can manage the extracted code ...")
