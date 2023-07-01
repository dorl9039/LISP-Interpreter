#!/usr/bin/env python3
"""6.009 Lab 8: Carlae (LISP) Interpreter"""

import doctest

# NO ADDITIONAL IMPORTS!


###########################
# Carlae-related Exceptions #
###########################


class CarlaeError(Exception):
    """
    A type of exception to be raised if there is an error with a Carlae
    program.  Should never be raised directly; rather, subclasses should be
    raised.
    """

    pass


class CarlaeSyntaxError(CarlaeError):
    """
    Exception to be raised when trying to evaluate a malformed expression.
    """

    pass


class CarlaeNameError(CarlaeError):
    """
    Exception to be raised when looking up a name that has not been defined.
    """

    pass


class CarlaeEvaluationError(CarlaeError):
    """
    Exception to be raised if there is an error during evaluation other than a
    CarlaeNameError.
    """

    pass


############################
# Tokenization and Parsing #
############################


def number_or_symbol(x):
    """
    Helper function: given a string, convert it to an integer or a float if
    possible; otherwise, return the string itself

    >>> number_or_symbol('8')
    8
    >>> number_or_symbol('-5.32')
    -5.32
    >>> number_or_symbol('1.2.3.4')
    '1.2.3.4'
    >>> number_or_symbol('x')
    'x'
    """
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            return x


_FORBIDDEN_CHARS = frozenset(("(", ")", " "))

def is_valid_variable_name(x):
    if not isinstance(x, str): return False
    if not isinstance(number_or_symbol(x), str): return False
    if any([c in x for c in _FORBIDDEN_CHARS]): return False
    return True


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a Carlae
                      expression
    """
    # indentation does not mater
    # comments are signaled by an "#", should not be included in result
    token_list = []
    token = ""
    comment_mode = False

    for char in source:
        if comment_mode:
            if char == '\n':
                comment_mode = False
            continue

        if char == "(":
            token_list.append(char)
            assert not token  # incorrect whitespace
        elif char in (" ", "\n", "#", ")"):
            if token:
                token_list.append(token)
            token = ""
            if char == "#":
                comment_mode = True
            elif char == ")":
                token_list.append(char)
        else: 
            token += char

    if token:
        token_list.append(token)

    return token_list


def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    def parse_sexpression(index):
        token = tokens[index]
        assert token == "("

        index += 1
        subexpression = []
        while index < len(tokens):
            if tokens[index] == ")":
                return subexpression, index + 1
            expression, index = parse_expression(index)
            subexpression.append(expression)
        raise CarlaeSyntaxError(f'Error: mismatched or missing parentheses.')

    def parse_expression(index):
        token = tokens[index]
        if token == "(":
            return parse_sexpression(index)
        if token == ")":
            raise CarlaeSyntaxError(f'Error: mismatched or missing parentheses.')
        rep = number_or_symbol(token)
        return rep, index + 1

    parsed_expression, idx = parse_expression(0)
    if idx != len(tokens):
        raise CarlaeSyntaxError(f'Error: malformed sexpression or mismatched parentheses.')
    return parsed_expression



######################
# Built-in Functions #
######################

def _mul(args):
    prod = 1
    for arg in args:
        prod *= arg
    return prod

def _div(args):
    if not args:
        raise CarlaeEvaluationError("Evaluation error: Division expected at least one argument")
    elif len(args) == 1:
        return 1 / args[0]
    else:
        return args[0] / _mul(args[1:])


class Environment:
    """
    Environment class, which allows assignment and lookup environment parentage
    """
    def __init__(self, local=None, parent=None):
        if local is None:
            local = {}
        self.local = local
        self.parent = parent


    def set_variable(self, name, expression):
        """
        Sets a variable (name) by creating in the local environment a dictionary key (name) associated 
        with a value (expression). Returns the value.
        """
        assert self.parent is not None
        if not is_valid_variable_name(name):
            raise CarlaeNameError(f'Error: {name} is not a valid variable name')
        self.local[name] = expression
        return self.local[name]
        
    def get_variable(self, name):
        """
        Looks in the local environment for the variable name, returns the value.
        If variable does not exist in the local environment and the environment has a parent,
        this looks up the variable name in the parent environment.
        If the variable does not exist in the local environment and the environment does not have a parent, 
        raises an error.
        """
        if not isinstance(name, str):
            raise CarlaeEvaluationError

        if name in self.local:
            return self.local[name]
        else:
            try:
                return self.parent.get_variable(name)
            except:
                raise CarlaeNameError(f"name '{name}' is not defined.")


def _make_builtins_env():
    builtins = {
        "+": sum,
        "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
        "*": _mul,
        "/": _div,
    }
    return Environment(local=builtins)


def make_global_env():
    builtins_env = _make_builtins_env()
    return Environment(parent=builtins_env)


class Function:
    """
    Function class, which allows storage of function details (code representing the expression, names
    of the function's parameters, and pointer to the function's enclosing environment) and calling 
    of function
    """
    def __init__(self, params, expr, environ):
        self.params = params
        self.expr = expr
        self.environ = environ

    def __call__(self, args):
        if len(self.params) != len(args):
            raise CarlaeEvaluationError("Error: parameter-argument number mismatch")
        # make a new environment whose parent is the function's enclosing environment (this is called lexical scoping).
        frame_environ = Environment(parent=self.environ)
        # in that new environment, bind the function's parameters to the arguments that are passed to it.
        for p, arg in zip(self.params, args):
            frame_environ.set_variable(p, arg)
        # evaluate the body of the function in that new environment.
        result = evaluate(self.expr, frame_environ)
        return result



##############
# Evaluation #
##############

def evaluate(tree, env=None):
    """
    Evaluate the given syntax tree according to the rules of the Carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    if env is None:
        env = make_global_env()

    # Case 1: s-expression.
    if type(tree) == list:
        op, args = tree[0], tree[1:]
        # Handles variable definitions. Returns the value of the defined variable
        if op == ":=":
            assert len(args) == 2
            name = args[0]
            if type(name) == list:
                equiv_tree = [op, name[0], ['function', name[1:], args[1]]]
                return evaluate(equiv_tree, env)
            else:
                expression = evaluate(args[1], env)
                return env.set_variable(name, expression)

        # Creates a new Function object.
        elif op == "function":
            assert len(args) == 2
            params = args[0]
            expr = args[1]
            func = Function(params, expr, env)
            return func

        else:
            if type(op) == list:
                # Anonymous function
                func = evaluate(op, env)
            else:
                # Named function
                func = env.get_variable(op)
            args = [evaluate(arg, env) for arg in args]
            return func(args)

    # Case 2: bare value
    elif type(tree) == int or type(tree) == float:
        return tree

    # Case 3: variable
    else:
        variable_value = env.get_variable(tree)
        return variable_value



def result_and_env(tree, env=None):
    """
    Takes the same argument as evaluate.
    Returns the result of the evaluation and the environment in which the expression was evaluated 
    as a tuple.
    """
    # If no environment is given as a parameter, makes a brand new environment which takes 
    # env_globals as its parent.
    if env is None:
        env = make_global_env()
    result = evaluate(tree, env)
    return result, env
    

def REPL(env):
    while True:
        source = input("in> ")
        if source == "EXIT":
            return
        else:
            tokens = tokenize(source)
            tree = parse(tokens)
            result = evaluate(tree, env)
            print("out>", result)
