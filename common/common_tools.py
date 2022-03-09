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
    y=abs(y)
    scaled_eps = eps * max(x, y)
    return diff <= scaled_eps

'''
def normalize_max(container, key, revert=False):
    elements = [elem[key] for elem in container]

    min_element = np.min(elements)
    max_element = np.max(elements)

    start_percent = 10
    end_percent = 30
    step_percent = 1
    clamp_min, clamp_max = -1.2, 1.2
    clamp_diff = clamp_max - clamp_min
    optimal_percent = start_percent

    elements = sorted(elements)
    #elements = np.ndarray(elements)
    max_distances = []
    std_deviations = []
    for throw_percent in range(start_percent, end_percent+1, step_percent):
        throw_one_side_count = int(np.ceil(len(elements) * throw_percent / 100.0))
        accounted_elements = np.ndarray(elements[throw_one_side_count+1:-throw_one_side_count])
        # элементы могут стать одинаковыми из-за клампа слишком большого их числа
        # а так же очень похожими из-за выброса в выборке
        # попробуем найти компромисс между максимальным разбросом
        # и минимальным расстоянием между двумя элементами
        max_distance = 0.0
        for i in range(len(accounted_elements)-1):
            distance = np.abs(accounted_elements[i] - accounted_elements[i-1])
            if distance > max_distance:
                max_distance = distance
        max_distances.append(max_distance)

        avg = np.average(accounted_elements)
        std_deviation = np.sqrt(np.average(np.power(avg - accounted_elements, 2)))
        std_deviations.append(std_deviation)
    max_distances = np.ndarray(max_distances)
    std_deviations = np.ndarray(std_deviations)

    min_dist, max_dist = np.min(max_distances), np.max(max_distances)
    min_deviation, max_deviation = np.min(std_deviations), np.max(std_deviations)

    max_distances = (max_distances - min_dist) / (max_dist - min_dist)
    std_deviations = (std_deviations - min_deviation) / (max_deviation - min_deviation)
'''


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
