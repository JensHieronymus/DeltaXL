"""Comparison of crosslink abundance between conditions."""


def fold_change(a, b):
    """Return the fold change from condition a to condition b (b / a).

    Raises ValueError if a is zero, since the fold change is undefined.
    """
    if a == 0:
        raise ValueError("Fold change is undefined when the reference abundance is 0.")
    return b / a
