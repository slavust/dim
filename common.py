import sympy as sp
import numpy as np


def power_cost(x):
    n, d = sp.fraction(sp.Rational(x))
    return abs(n) + abs(d)


def clamp(minimum, maximum, x):
    return min(maximum, max(minimum, x))


def nearly_equal(x, y):
    eps = np.finfo(float).eps
    diff = abs(x-y)
    x = abs(x)
    y = abs(y)
    scaled_eps = eps * max(x, y)
    return diff <= scaled_eps


def normalize_80(container, key, revert=False):
    """
    normalization based on 80% of elements
    """
    elements = [elem[key] for elem in container if key in elem]
    elements.sort()
    ten_percent_count = int(len(elements) * 0.01 * 10)
    assert ten_percent_count * 2 < len(elements)
    elements = elements[ten_percent_count:len(elements)-ten_percent_count]
    maximum = max(elements)
    minimum = min(elements)
    clamp_min, clamp_max = -0.2, 1.2

    if maximum == minimum:
        for elem in container:
            elem[key] = 0.5
        return

    if not revert:
        for elem in container:
            # todo: optional exception?
            if key not in elem:
                continue
            elem[key] = clamp(clamp_min, clamp_max, (elem[key] - minimum) / (maximum - minimum))
    else:
        elements = np.ndarray((len(container), 1), dtype=np.float128)
        for i, elem in enumerate(container):
            if key not in elem:
                assert False
            elements[i] = elem[key]
        elements = np.clip(1.0 - (elements - minimum) / (maximum-minimum), clamp_min, clamp_max)
        for i, elem in enumerate(container):
            if key not in elem:
                assert False
            elem[key] = float(elements[i])
