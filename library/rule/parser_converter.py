from library.rule.parser import parse, Rule

"""
Rule Class
rule['action']
rule['header']
...
...
...
"""


def parse_line(p_rule_line: str):
    line = p_rule_line.rstrip()
    return parse(line)


def rule_cls_to_str(p_rule: Rule):
    return str(p_rule)


def rule_cls_to_dict(p_rule: Rule):
    return dict(p_rule)
