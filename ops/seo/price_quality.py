"""Publication rules shared by price guides, checkers and dated report exports.

Condition statistics are a different population from the overall search. Never
promote them to an overall estimate or replace a measured quartile to pass a rule.
"""


def has_ordered_price(view):
    span = view.get('range_cents') or {}
    values = (span.get('low'), view.get('typical_cents'), span.get('high'))
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in values) and values[0] <= values[1] <= values[2]


def publishable_overall(view, minimum=100):
    return bool(view and not view.get('provisional')
                and view.get('display_verdict') == 'ok'
                and view.get('confidence') in ('medium', 'high')
                and (view.get('sample_size') or 0) >= minimum
                and has_ordered_price(view))


def publishable_conditions(view, minimum=10):
    return [c for c in view.get('by_condition') or []
            if c.get('verdict') == 'ok'
            and (c.get('sample_size') or 0) >= minimum
            and has_ordered_price(c)]
