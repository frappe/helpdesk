"""Custom Cosmic Ray mutation operators derived from the Helpdesk business rules.

The core operators mutate syntax (==/!=, and/or, numbers). They cannot express
the two mistakes that matter most in the ticket rules:

* confusing one ticket status or status category with another (BR1, BR3, BR4);
* getting the agent exemption wrong, so that a customer is treated as an agent
  or an agent as a customer (BR2, BR4).

Each operator below injects exactly one such domain fault per mutant.
"""

from cosmic_ray.operators.operator import Example, Operator
from parso.python.tree import Keyword, Name, String

# Each status value is replaced by the value a developer would most plausibly
# confuse it with. "Closed" is a status *inside* the Resolved category, which is
# exactly the distinction BR3 and BR4 turn on.
STATUS_SWAPS = {
    "Resolved": "Open",
    "Closed": "Resolved",
    "Open": "Resolved",
    "Paused": "Open",
}


class SwapTicketStatus(Operator):
    """Replace a ticket status / status-category literal with a different one."""

    def mutation_positions(self, node):
        if isinstance(node, String) and _unquote(node.value) in STATUS_SWAPS:
            yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        quote = node.value[0]
        replacement = STATUS_SWAPS[_unquote(node.value)]
        return String(f"{quote}{replacement}{quote}", node.start_pos, prefix=node.prefix)

    @classmethod
    def examples(cls):
        return (
            Example('x = "Resolved"', 'x = "Open"'),
            Example("if status == 'Closed': pass", "if status == 'Resolved': pass"),
            Example('a = "Open"; b = "Paused"', 'a = "Open"; b = "Open"', occurrence=1),
        )


class _ReplaceIsAgentCall(Operator):
    """Replace a call `is_agent()` (no arguments) with a constant."""

    constant = None

    def mutation_positions(self, node):
        if _is_agent_call(node):
            yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        return Keyword(self.constant, node.start_pos, prefix=node.get_first_leaf().prefix)


class RevokeAgentExemption(_ReplaceIsAgentCall):
    """`is_agent()` -> `False`: agents are held to the customer restrictions."""

    constant = "False"

    @classmethod
    def examples(cls):
        return (
            Example("if x or is_agent(): pass", "if x or False: pass"),
            Example("y = is_agent()", "y = False"),
        )


class GrantAgentExemption(_ReplaceIsAgentCall):
    """`is_agent()` -> `True`: customers get the agent's exemption."""

    constant = "True"

    @classmethod
    def examples(cls):
        return (
            Example("if x or is_agent(): pass", "if x or True: pass"),
            Example("y = is_agent()", "y = True"),
        )


def _unquote(literal):
    if len(literal) >= 2 and literal[0] in "\"'" and literal[-1] == literal[0]:
        return literal[1:-1]
    return None


def _is_agent_call(node):
    if getattr(node, "type", None) != "atom_expr" or len(node.children) != 2:
        return False
    target, trailer = node.children
    return (
        isinstance(target, Name)
        and target.value == "is_agent"
        and trailer.type == "trailer"
        and trailer.get_code().strip() == "()"
    )


_OPERATORS = {
    op.__name__: op for op in (SwapTicketStatus, RevokeAgentExemption, GrantAgentExemption)
}


class OperatorProvider:
    """Cosmic Ray operator-provider plugin (entry point name: `sqe`)."""

    def __iter__(self):
        return iter(_OPERATORS)

    def __getitem__(self, name):
        return _OPERATORS[name]


__all__ = ["GrantAgentExemption", "OperatorProvider", "RevokeAgentExemption", "SwapTicketStatus"]
