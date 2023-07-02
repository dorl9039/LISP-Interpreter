# Project description
Penultimate lab assignment in MIT's 6.009: Fundamentals of Programming. The course provided a test suite and basic scaffolding, and I implemented lab.py, which is the core interpreter logic.

The goal is to create _carlae_, an interpreter for a Turing-complete subset of LISP with support for lexically scoped functions. The syntax for _carlae_ can be grouped into two types:
- **Atomic expression**: numbers and symbols (e.g., variable names or operators like `+`) that cannot be broken into pieces.
- **S-expression**: zero or more expressions enclosed within parentheses. The first subexpression defines the S-expression. Subexpressions can be further grouped into two types:
    - _special form_: starts with a keyword, which can be one of the following two: `function` for creating function objects, and `:=` for defining variables.
    - function call: starts with a non-keyword, indicating that the first element in the expression is the function to be called, and the remaining subexpressions are the arguments to that function.

## Components
### Tokenizer
- Takes a single string representing a program and outputs a list of string tokens.
- Handles comments: e.g., if a line contains a `#`, the tokenizer does not consider the `#` and the following characters to be part of the input.
### Parser
- Takes a list of tokens and outputs an abstract syntax tree
- Raises an error if expression parentheses are mismatched
### Evaluator
- Runs programs by taking an abstract syntax tree and returns the value of the expression.

## Features
### Calculator
Evaluates arithmetic (`+`, `-`, `*`, `/`) expressions with arbitrarily many arguments. Adheres to the order of operations.
### Environments
Maintains contexts in which an expression should be evaluated. An environment consists of bindings from variable names to values and references a parent environment (if one exists) from which other bindings are inherited. 
### Conditionals
Supports conditional executionm e.g., `(if COND TRUE_EXP FALSE_EXP)`
### Booleans and comparisons
Evaluates truthiness of expressions. `and` and `or` are implemented to "short-circuit", that is, evaluate only as far as necessary to determine what the result should be.
### Lists
Implements linked lists using a Python class, which has class methods for built-in list functions, for example:
- return the element at a given index
- concatenate an arbitrary number of lists
- map a function to each element in a given list
- filter a given list
- reduce a given list 
### Evaluating multiple expressions
Allows for running commands successively. Expressions are run sequentially, and only the result of the last expression is returned.
### Variable binding manipulation
Enables object-oriented programming within _carlae_
- del: deletes variable bindings within the current environment
- let: creates local variable definitions which cannot be accessed outside the expression
- set!: changes the value of an existing variable

## Example programs
```
in>  (+ 4 5 (- 2 (* 2 3)))
out> 5
```
```
in>  (:= x (/ 127 3)
out> 42.333333333333336
```
```
in>  (:= (fib n) (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2)))))
out> <__main__.Function object at 0x10ce52ad0>
in>  (fib 20)
out> 6765
```
```
in>  (and (=? 2 2) (< 10 3))
out> False
```
```
in>  (:= arr (list 1 2 3 4 5 6 7 8))
out> <__main__.Pair object at 0x10f16ab00>
in>  (reduce + (map (function (i) (* i i)) (filter (function (i) (< i 5)) arr)) 0)
out> 30
```

## Skills practiced
- Object-oriented programming
- Functional programming


