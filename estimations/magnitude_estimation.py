import numpy as np


def make_magnitude_penalty(evaluated_unknown_points):
    max_value = np.max(np.abs(evaluated_unknown_points), axis=-1)
    return max_value

def make_avg_derivative_magnitude_estimation(param, evaluated_unknown_points):
    table_X, table_Y = param, evaluated_unknown_points

    dxdy_avg = (table_Y[-1] - table_Y[0]) / (table_X[-1] - table_X[0])
    return abs(dxdy_avg)