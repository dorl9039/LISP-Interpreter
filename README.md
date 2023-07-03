# Project description
Personal project based on the penultimate lab assignment in the Spring 2022 edition of MIT's 6.009: Fundamentals of Programming. The goal is to create _carlae_, an interpreter for a Turing-complete subset of LISP with support for lexically scoped functions. The final product supports a number of advanced language features, such as lexical scopes, recursive functions, and higher order functions. The course provided a test suite and basic scaffolding, and I implemented lab.py, which is the core interpreter logic.

## Takeaways
I found that implementing a parser and interpreter from scratch significantly improved my understanding about how programming languages work in general. For instance, I have a better appreciation for lexical scoping with anonymous functions in Python, and I now know the mechanism behind why too much recursion leads to a stack overflow error. 

I also can now genuinely laugh at this [xkcd comic](https://xkcd.com/297).

## Components
### Tokenizer
- Takes a single string representing a program and outputs a list of string tokens.
- Handles comments: e.g., if a line contains a `#`, the tokenizer does not consider the `#` and the following characters to be part of the input.
### Parser
- Takes a list of tokens and outputs an abstract syntax tree
- Raises an error if expression is malformed
### Evaluator
- Runs programs by taking an abstract syntax tree and returns the value of the expression.

## Features

### Arithmetic
Evaluates basic arithmetic (`+`, `-`, `*`, `/`) expressions. Arithmetic operators extend to arbitrarily many arguments via reduce-like behavior, e.g., `(+ 1 2 3)` evaluates to 6.

### Booleans, comparisons, and conditionals
Evaluates truthiness of expressions. `and` and `or` are implemented to "short-circuit", that is, evaluate only as far as necessary to determine what the result should be.
Supports conditional execution e.g., `(if COND TRUE_EXP FALSE_EXP)`

### Lists
Implements linked lists with built-in functions, for example:
- return the element at a given index
- concatenate an arbitrary number of lists
- map a function to each element in a given list
- filter a given list
- reduce a given list

### Lexical scoping
Maintains contexts in which an expression should be evaluated using lexical scoping rules. An environment consists of bindings from variable names to values. Undefined bindings can be inherited from the parent environment (if one exists). The way this is implemented also enables support for recursion!

### Variable binding manipulation
Enables object-oriented programming within _carlae_
- del: deletes variable bindings within the current environment
- let: creates local variable definitions which cannot be accessed outside the expression
- set!: changes the value of an existing variable

## Example expressions

The language supports arithmetic operations (written in Polish notation), conditionals, and variable assignments.
```
in>  (+ 4 5 (- 2 (* 2 3)))
out> 5

in>  (and (=? 2 2) (< 10 3))
out> False

in>  (:= x (/ 127 3)
out> 42.333333333333336
```

The way lexical scopes and function calls are handled also allows for recursive function definitions.
```
in>  (:= (fib n) (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2)))))
out> <__main__.Function object at 0x10ce52ad0>
in>  (fib 20)
out> 6765
```

I also implemented some built-in higher order functions such as map, reduce, and filter. For instance, this function evaluates the sum of the square of all elements less than 5 in a list.
```
in>  (:= arr (list 1 2 3 4 5 6 7 8))
out> <__main__.Pair object at 0x10f16ab00>
in>  (reduce + (map (function (i) (* i i)) (filter (function (i) (< i 5)) arr)) 0)
out> 30
```

## Skills practiced
- Object-oriented programming
- Functional programming


