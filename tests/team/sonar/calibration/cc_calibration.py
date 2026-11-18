"""Calibration file: one construct per function, to see which ones SonarQube's
Python analyser adds to cyclomatic complexity (run_calibration.sh).
Each function's expected value under the textbook rule "decisions + 1" is
given in its name's comment. Not part of the product."""


def only_straight_line(a):  # textbook 1
    return a + 1


def one_if(a):  # textbook 2
    if a:
        return 1
    return 0


def one_or(a, b):  # textbook 2
    return a or b


def one_and(a, b):  # textbook 2
    return a and b


def one_conditional_expression(a):  # textbook 2
    return "s" if a > 1 else ""


def one_for(items):  # textbook 2
    total = 0
    for item in items:
        total += item
    return total


def one_except(action):  # textbook 2
    try:
        action()
    except ValueError:
        return False
    return True


def two_excepts(action):  # textbook 3
    try:
        action()
    except ValueError:
        return 1
    except KeyError:
        return 2
    return 0


def one_while(n):  # textbook 2
    while n > 0:
        n -= 1
    return n


def one_elif(a):  # textbook 3
    if a == 1:
        return "one"
    elif a == 2:
        return "two"
    return "many"


def one_comprehension_if(items):  # textbook 3 (for + if)
    return [i for i in items if i]


def one_continue_in_loop(items):  # textbook 3 (for + if); continue is not a decision
    for item in items:
        if item:
            continue
    return items
