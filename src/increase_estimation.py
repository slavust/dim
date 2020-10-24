import numpy as np
from common_tools import nearly_equal

def make_increase_estimation(unknown_component_points):
    table_Y = unknown_component_points

    y0, yn = table_Y[0], table_Y[-1]
    if nearly_equal(y0, yn):
        return 0.5
    return 1.0 if yn > y0 else 0.0


