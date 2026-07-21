import pandas as pd


class RuleEngine:

    @staticmethod
    def compare(left, operator, right):

        if operator == ">":
            return left > right

        if operator == "<":
            return left < right

        if operator == ">=":
            return left >= right

        if operator == "<=":
            return left <= right

        if operator == "==":
            return left == right

        if operator == "!=":
            return left != right

        if operator == "cross_above":
            return (left.shift(1) <= right.shift(1)) & (left > right)

        if operator == "cross_below":
            return (left.shift(1) >= right.shift(1)) & (left < right)

        raise ValueError(f"Unknown operator: {operator}")

    @staticmethod
    def resolve_operand(operand, indicator_values, df):

        operand_type = operand["type"]

        if operand_type == "indicator":
            return indicator_values[operand["name"]]

        if operand_type == "ohlc":
            return df[operand["name"].capitalize()]

        if operand_type == "value":
            return operand["value"]

        raise ValueError(f"Unknown operand type: {operand_type}")

    @staticmethod
    def evaluate_condition(condition, indicator_values, df):

        left = RuleEngine.resolve_operand(
            condition["left"],
            indicator_values,
            df,
        )

        right = RuleEngine.resolve_operand(
            condition["right"],
            indicator_values,
            df,
        )

        return RuleEngine.compare(
            left,
            condition["op"],
            right,
        )