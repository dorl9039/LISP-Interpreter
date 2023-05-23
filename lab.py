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
    comment_string = ""
    comment_mode = False

    for char in source:
        if char == "#":
            comment_mode = True

        if char == '\n':
            comment_mode = False

        if comment_mode:
            continue

        if char == "(":
            token_list.append(char)
        elif char == ")":
            if token:
                token_list.append(token)
            token_list.append(char)
            token = ""

        elif char == " " or char == "\n":
            if token:
                token_list.append(token)
            token = ""

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
    right_count = 0
    left_count = 0

    for token in tokens:
        if token == "(":
            right_count += 1
        if token == ")":
            left_count += 1
    if (right_count != left_count):
        raise CarlaeSyntaxError("Error: number of parentheses do not match")
    elif right_count == 0:
        if ":=" in tokens:
            raise CarlaeSyntaxError("Error: missing parentheses for S-expression")



    def parse_expression(index):
        """
        Returns a tuple. The first element is the parsed expression:
        - numbers (int or floats) or symbols as base cases.
        - recursively returns S-expressions as lists of numbers or symbols.
        The second element is the index of the token following the parsed expression.
        """
        token = tokens[index]

        # next_index always holds the index of the token to-be-parsed next
        next_index = index + 1
        rep = number_or_symbol(token)
        print()
        print(f'call parse_expression({index}), got {type(rep)}, {rep}')

        # raises CarlaeSyntaxError if parentheses are mismatched or missing
        if rep == ")":
             raise CarlaeSyntaxError(f'Error: mismatched or missing parentheses. Rep is {rep}')

        # base case returns a tuple of: numbers or symbols and the index of the next token
        if rep != "(" and rep != ")":
            print(f'rep is not ( or ), returned {rep}, {next_index}')
            return (rep, next_index)

        subexpression = []

        while tokens[next_index] != ")":
            element, next_index = parse_expression(next_index)
            subexpression.append(element)
        return (subexpression, next_index + 1)



    parsed_expression, next_index = parse_expression(0)
    print(f'parsed_expression: {parsed_expression}, next_index: {next_index}')
    return parsed_expression



######################
# Built-in Functions #
######################

class environment:
    """
    Environment class, which allows assignment and lookup environment parentage
    """
    def mul(args):
        prod = 1
        for arg in args:
            prod *= arg
        return prod

    def div(args):
        if not args:
            raise CarlaeEvaluationError("Evaluation error: Division expected at least one argument")
        elif len(args) == 1:
            return 1 / args[0]
        else:
            return args[0] / environment.mul(args[1:])
    carlae_builtins = {
        "+": sum,
        "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
        "*": mul,
        "/": div,
    }    

    def __init__(self, local, parent):
        self.local = {}
        self.parent = parent


    def set_variable(self, name, expression):
        self.local[name] = expression
        return self.local[name]
        
    def get_variable(self, name, environ):
        if name in environ.local:
            return environ.local[name]
        else:
            environ = environ.parent
            try:
                return self.get_variable(name, environ)
            except:
                raise CarlaeNameError(f'variable {name} does not has no value')


##############
# Evaluation #
##############
builtins = environment(environment.carlae_builtins, None)
env_globals = environment("empty", builtins)

def evaluate(tree, local = env_globals):
    """
    Evaluate the given syntax tree according to the rules of the Carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    
    # base cases: returns associated symbol in carlae_builtins or a number
    
    if type(tree) == list:
         
        op = tree[0]
        if op == ":=":
            name = tree[1]
            expression = evaluate(tree[2], local)            
            return local.set_variable(name, expression)

        elif op not in environment.carlae_builtins:
            raise CarlaeEvaluationError(f'Error: {op} is not a valid function')

        else:
            args = []
            for element in tree[1:]:
                exp = evaluate(element, local)
                args.append(exp)
            return environment.carlae_builtins[op](args)

    elif tree in environment.carlae_builtins:
        return environment.carlae_builtins[tree]
    
    elif type(tree) == int or type(tree) == float:
        return tree

    elif tree.isidentifier():
        variable_value = local.get_variable(tree, local)
        return variable_value

    else: 
        raise CarlaeNameError(f'Error: {tree} is not a symbol in carlae_builtins')

def result_and_env(tree, local = env_globals):
    """
    Takes the same argument as evaluate.
    Returns the result of the evaluation and the environment in which the expression was evaluated as a tuple.
    """
    if local == env_globals:
        local = environment("local", env_globals)

    result = evaluate(tree, local)
    
    return(result, local)
    


def REPL():
    # initialize global environment here
    source = input("in> ")
    if source == "EXIT":
        return
    else:
        tokens = tokenize(source)
        tree = parse(tokens)
        result = evaluate(tree)
        print("out>", result)
        return REPL()
