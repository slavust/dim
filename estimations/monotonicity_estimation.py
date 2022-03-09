import common_tools as ct
import numpy as np
from scipy.interpolate import UnivariateSpline

def make_non_monothonicity_estimation(param, unknown_component_points, dbg_figname=None):
    table_X, table_Y = param, unknown_component_points
    domain = np.min(table_X), np.max(table_X)
    min_y, max_y = np.min(table_Y), np.max(table_Y)
    #if min_y == max_y:
    #    return 1.0

    # todo: x already in [0, 1]
    X_normalized = table_X
    Y_normalized = [(y - min_y) / (max_y - min_y) for y in table_Y]

    derivatives = []
    for i in range(0, len(Y_normalized)-1):
        dy = (Y_normalized[i+1] - Y_normalized[i])
        dx = (X_normalized[i+1] - X_normalized[i])
        assert dx != 0
        dydx = dy / dx
        derivatives.append(dydx)

    sum_positive = sum(d for d in derivatives if d > 0)
    sum_negative = sum(d for d in derivatives if d < 0)

    estimation = abs(min(sum_negative, sum_positive))

    return estimation