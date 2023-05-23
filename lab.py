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
        raise CarlaeSyntaxError(CarlaeError)


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
        #print(f'call parse_expression({index}), got {type(rep)}, {rep}')

        # raises CarlaeSyntaxError if parentheses are mismatched or missing
        if rep == ")" or rep == ":=":
             raise CarlaeSyntaxError(CarlaeError)

        # base case returns a tuple of: numbers or symbols and the index of the next token
        if rep != "(" and rep != ")":
            return (rep, next_index)
        

        subexpression = []
        
        while tokens[next_index] != ")":
            element, next_index = parse_expression(next_index)
            subexpression.append(element)
        return (subexpression, next_index + 1)

    parsed_expression = parse_expression(0)[0]
    return parsed_expression



######################
# Built-in Functions #
######################


carlae_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
}


##############
# Evaluation #
##############


def evaluate(tree):
    """
    Evaluate the given syntax tree according to the rules of the Carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    # base cases: returns associated symbol in carlae_builtins or a number
    if tree == "+" or tree == "-":
        print('entered single operand loop')
        return carlae_builtins[tree]
    elif type(tree) == int or type(tree) == float:
        return tree
   
    # recursively evaluates S-expressions by calling the first element with the remaining
    # elements passed in as arguments

    if type(tree) == list:
        op = tree[0]
        if op not in carlae_builtins:
            raise CarlaeEvaluationError(f'Error: {op} is not a valid function')
        args = []
        for element in tree[1:]:
            exp = evaluate(element)
            args.append(exp)
        return carlae_builtins[op](args)

    # Raises error for undefined expression
    if tree not in carlae_builtins:
        raise CarlaeNameError(f'Error: {tree} is not a symbol in carlae_builtins')
