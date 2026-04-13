import math

def mean(values):
    """
    Compute the arithmetic mean of the given values.

    Args:
        values: An iterable of numeric values.

    Returns:
        The arithmetic mean as a float.

    Raises:
        ValueError: If `values` is empty.
    """
    vals = list(values)
    if not vals:
        raise ValueError("mean() requires at least one value")
    return sum(vals) / len(vals)


def stddev_sample(values):
    """
    Compute sample standard deviation (ddof=1), matching your original logic.

    Args:
        values: An iterable of numeric values.

    Returns:
        Standard deviation of the sample as a float.

    Raises:
        ValueError: if fewer than 2 values are provided.
    """
    vals = list(values)
    n = len(vals)
    if n < 2:
        raise ValueError("stddev_sample() requires at least two values")

    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (n - 1))


def summarize(values):
    """
    Compute summary statistics (mean and sample standard deviation) for the given values.

    This is a convenience wrapper around `mean()` and `stddev_sample()`.

    Args:
        values: An iterable of numeric values.

    Returns:
        A tuple `(mean_value, stddev_value)` where:
          - `mean_value` is the arithmetic mean of `values`
          - `stddev_value` is the sample standard deviation of `values` (ddof=1)

    Raises:
        ValueError: If `values` is empty (mean undefined).
        ValueError: If `values` contains fewer than 2 elements (sample std dev undefined).
    """
    vals = list(values)
    return mean(vals), stddev_sample(vals)
