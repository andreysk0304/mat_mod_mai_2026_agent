from __future__ import annotations

import ast

from agent.tool_api import JsonDict, tool


def _safe_eval_arithmetic(expression: str) -> float:
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Constant,
    )

    def _eval(node: ast.AST) -> float:
        if not isinstance(node, allowed_nodes):
            raise ValueError("Only arithmetic expressions are allowed")
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return value
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left**right
            if isinstance(node.op, ast.Mod):
                return left % right
        raise ValueError("Unsupported expression")

    tree = ast.parse(expression, mode="eval")
    return _eval(tree)


@tool(
    name="calculate",
    description="Evaluate a basic arithmetic expression.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Arithmetic expression like '(2 + 3) * 4'",
            }
        },
        "required": ["expression"],
        "additionalProperties": False,
    },
)
def calculate(arguments: JsonDict) -> JsonDict:
    expression = str(arguments.get("expression", "")).strip()
    if not expression:
        raise ValueError("expression is required")
    result = _safe_eval_arithmetic(expression)
    return {"expression": expression, "result": result}
