"""6.009 Lab 9: Carlae Interpreter Part 2"""

import sys
sys.setrecursionlimit(10_000)

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


    def set_bang(self, name, expression):
        if name in self.local:
            self.local[name] = expression
            return self.local[name]
        else:
            try:
                return self.parent.set_bang(name, expression)
            except:
                raise CarlaeNameError(f'variable is not defined in any environments in the chain')


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


COMPARE_SYMBOLS = {
    '=?': lambda x, y: x == y,
    '>': lambda x, y: x > y,
    '>=': lambda x, y: x >= y,
    '<': lambda x, y: x < y,
    '<=': lambda x, y: x <= y,
    }

def _compare(symbol, args):
    for arg1, arg2 in zip(args, args[1:]):
        if not COMPARE_SYMBOLS[symbol](arg1, arg2):
            return False
    return True


def _not(args):
    if len(args) != 1:
        raise CarlaeEvaluationError("Error: more than one argument passed in")
    
    for arg in args:
        if arg == True:
            return False
        elif arg == False:
            return True


def _pair(args):
    if len(args) != 2:
        raise CarlaeEvaluationError("Error: pair only takes 2 arguments")
    
    new_pair = Pair(args[0], args[1])
    return new_pair


def _get_head(args):
    if len(args) != 1:
        raise CarlaeEvaluationError("Error: wrong number of arguments provided")
    
    pair = args[0]
    if not isinstance(pair, Pair):
        raise CarlaeEvaluationError('Error: not a Pair object')
    return pair.head


def _get_tail(args):
    if len(args) != 1:
        raise CarlaeEvaluationError("Error: wrong number of arguments provided")
    
    pair = args[0]
    if not isinstance(pair, Pair):
        raise CarlaeEvaluationError("Error: not a Pair object")
    return pair.tail


def _list(args):
    if len(args) == 0:
        return Nil()
    else:
        return Pair(args[0], _list(args[1:]))


def _is_list(args):
    if len(args) != 1:
        raise CarlaeEvaluationError("Error: list? takes only one argument")
    obj = args[0]

    def __is_list(o):
        if isinstance(o, Nil):
            return True
        elif isinstance(o, Pair):
            return __is_list(o.tail)
        return False

    return __is_list(obj)


def _list_length(args):
    if not _is_list(args):
        raise CarlaeEvaluationError("Error: object is not a linked list")
    obj = args[0]    
    
    if isinstance(obj, Nil):
        return 0
    length = 1 + _list_length([obj.tail])

    return length


def _index_list(args):
    """
    Takes a list and a nonnegative index as arguments. Returns the element at the given index
    in the given list
    """
    lst = args[0]
    target_idx = args[1]
    count = 0
    try:
        while True:
            target = lst.head
            if count == target_idx:
                return target
            else:
                count += 1
                lst = lst.tail
    except: 
        raise CarlaeEvaluationError("Error: index out of range")


def _print_list(o, max_depth=-1):
    if max_depth == 0:
        print("max depth reached")
        return

    if isinstance(o, Nil):
        print(o)
    elif isinstance(o, Pair):
        print("o", o)
        print("  > head", o.head)
        print("  > tail", o.tail)
        _print_list(o.tail, max_depth=max_depth-1)


def _copy_list(ll):
    """
    Takes a linked list as argument. Returns a copy of the given list as another linked list.
    If the given linked list is empty, returns an empty list.
    """
    if isinstance(ll, Nil):
        return Nil()
    return Pair(ll.head, _copy_list(ll.tail))


def _concat_list(args):
    """
    Takes an arbitrary number of lists as arguments. Returns a new list representing the
    concatenation of the given lists.
    If exactly one list is passed in, returns a copy of that list.
    If called with no arguemtns, returns an empty list.
    """
    depth = len(args)
    def _print(*a):
        print(f"{depth} | {a}")    
    
    if len(args) == 0:
        return Nil()

    first_list, rest_of_lists = args[0], args[1:]
    if not _is_list([first_list]):
        raise CarlaeEvaluationError("Error: can only concat lists")  

    if isinstance(first_list, Nil):
        return _concat_list(rest_of_lists)   

    new_list = _copy_list(first_list)
    next_pair = new_list

    while not isinstance(next_pair.tail, Nil):
        next_pair = next_pair.tail

    next_pair.tail = _concat_list(rest_of_lists)

    return new_list


def _map(args):
    """
    Takes as arguments a function and a list. Returns a new list containing the results of applying 
    the given function to eawch element of the given list.
    """
    if len(args) != 2:
        raise CarlaeEvaluationError("Error: incorrect number of arguments")
    
    func, lst = args[0], args[1]
    
    if not _is_list([lst]):
        raise CarlaeEvaluationError("Error: second argument is not a list")

    # Base case for when the function reaches the end of a linked list.
    if isinstance(lst, Nil): 
        return Nil()
    # Calls the given function on the head of the linked list and sets the result as the head of the new list.
    # Tail of new list recursively calls _map through the rest of the linked list.
    new_list = Pair(func([lst.head]), _map([func, lst.tail]))

    return new_list


def _filter(args):
    """
    Takes as arguments a function and a list. Returns a new list containing only the elements of
    the given list for which the given function returns true.
    """
    if len(args) != 2:
        raise CarlaeEvaluationError("Error: incorrect number of arguments")

    func, lst = args[0], args[1]

    if not _is_list([lst]):
        raise CarlaeEvaluationError("Error: second argument is not a list")

    if isinstance(lst, Nil):
        return Nil()

    tail_filtered = _filter([func, lst.tail])
    if func([lst.head]) == True:
        new_list = Pair(lst.head, tail_filtered) 
    else:
        new_list = tail_filtered

    return new_list


def _reduce(args):
    """
    Takes as arguments a function, a list, and an initial value. Returns a number that is produced
    by successively applying the given function to elements in the list, maintaining an
    intermediate result along the way.
    """
    if len(args) != 3:
        raise CarlaeEvaluationError("Error: incorrect number of arguments")

    func, lst, initval = args[0], args[1], args[2]

    if not _is_list([lst]):
        raise CarlaeEvaluationError("Error: second argument is not a list")

    if isinstance(lst, Nil):
        return initval

    initval = func([initval, lst.head])
    lst = lst.tail
    return _reduce([func, lst, initval])


def _begin(args):
    """
    Evaluates all the arguments successively. Returns the last argument.
    """
    return args[-1]


class Nil:
    def __eq__(self, other):
        if isinstance(other, Nil):
            return True
        return False


def _make_builtins_env():
    builtins = {
        "+": sum,
        "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
        "*": _mul,
        "/": _div,
        "@t": True,
        "@f": False,
        "not": _not,
        "=?": lambda args: _compare("=?", args),
        ">": lambda args: _compare(">", args),
        ">=": lambda args: _compare(">=", args),
        "<": lambda args: _compare("<", args),
        "<=": lambda args: _compare("<=", args),
        "head": _get_head,
        "tail": _get_tail,
        "nil": Nil(),
        "pair": _pair,
        "list": _list,
        "list?": _is_list,
        "length": _list_length,
        "nth": _index_list,
        "concat": _concat_list,
        "map": _map,
        "filter": _filter,
        "reduce": _reduce,
        "begin": _begin,

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


class Pair:
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail


    def __eq__(self, other):
        if not isinstance(other, Pair):
            return False
        elif self.head == other.head and self.tail == other.tail: 
            return True
        return False




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
        if len(tree) == 0:
            raise CarlaeEvaluationError('Error: empty subexpression')

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

        # Handles conditional forms
        elif op == "if":
            cond = args[0]
            true_exp = args[1]
            false_exp = args[2]
            if evaluate(cond, env) == True:
                return evaluate(true_exp, env)
            else:
                return evaluate(false_exp, env)

        elif op == 'and':
            for arg in args:
                if evaluate(arg, env) == False:
                    return False
            return True

        elif op == 'or':
            for arg in args:
                if evaluate(arg, env) == True:
                    return True
            return False
        
        # Deletes variable bindings within the current environment
        elif op == "del":
            if len(args) != 1:
                raise CarlaeEvaluationError("Error: there should only be one variable")
            var = args[0]
            if var not in env.local:
                raise CarlaeNameError("Var is not bound in the current environment")
            return env.local.pop(var)
        
        # Creates local variable definitions, which are only available in the body of the "let" expression
        elif op == "let":
            if len(args) != 2:
                raise CarlaeEvaluationError("Error: wrong number of arguments")
            vars_vals, body = args[0], args[1]
            local_env = Environment(parent = env)
            for var_val in vars_vals:
                var, val = var_val[0], evaluate(var_val[1], env)
                local_env.set_variable(var, val)
            return evaluate(body, local_env)

        # Changes the value of an existing variable
        elif op == "set!":
            if len(args) != 2:
                raise CarlaeEvaluationError("Error: wrong number of arguments")
            var, expr = args[0], evaluate(args[1], env)
            # how to find the environment?
            return env.set_bang(var, expr)

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


def evaluate_file(file_name, env=None):
    """
    Takes as a single argument a file name (string) and an optional argument for the environment 
    in which to evaluate the expression. Returns the result of evaluating the expression contained
    in the file. 
    """
    file_object = open(file_name)
    file_line = file_object.read()
    tokens = tokenize(file_line)
    tree = parse(tokens)
    
    return evaluate(tree, env)


