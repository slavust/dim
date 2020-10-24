import unittest
import numpy as np
import common_tools

import linearity_estimation
import periodicity_estimation
import monotonicity_estimation
import magnitude_estimation
import increase_estimation


def create_line_func(slope, offset):
    X = np.arange(0.0, 1.0, 0.05)
    Y = np.array([x*slope + offset for x in X])
    return X, Y


def create_power_func(cf, power):
    X = np.arange(0.0, 1.0, 0.05)
    Y = np.array([cf*(x**power) for x in X])
    return X, Y


def create_periodic_func(scale, offset):
    X = np.arange(0.0, 1.0, 0.05)
    Y = scale*np.sin(X*4.0) + offset
    return X, Y


class TestEstimations(unittest.TestCase):
    def test_linearity(self):
        line_x, line_y = create_line_func(2.0, 3.0)
        line_estim = linearity_estimation.make_linearity_estimation(line_x, line_y)

        pow_x, pow_y = create_power_func(1.0, 3)
        pow_estim = linearity_estimation.make_linearity_estimation(pow_x, pow_y)
        assert line_estim > pow_estim

        periodic_x, periodic_y = create_periodic_func(2.0, 0.0)
        periodic_estim = linearity_estimation.make_linearity_estimation(periodic_x, periodic_y)
        assert pow_estim > periodic_estim

    def test_periodicity(self):
        line_x, line_y = create_line_func(2.0, 3.0)
        line_estim = periodicity_estimation.make_periodicity_estimation(line_x, line_y)
        periodic_x, periodic_y = create_periodic_func(2.0, 3.0)
        periodic_estim = periodicity_estimation.make_periodicity_estimation(periodic_x, periodic_y)
        assert periodic_estim > line_estim

    def test_monotonicity(self):
        line_x, line_y = create_line_func(2.0, 3.0)
        non_monotonicity_line = periodicity_estimation.make_periodicity_estimation(line_x, line_y)
        periodic_x, periodic_y = create_periodic_func(2.0, 3.0)
        non_monotonicity_periodic = monotonicity_estimation.make_non_monothonicity_estimation(periodic_x, periodic_y)
        assert non_monotonicity_periodic > non_monotonicity_line

    def test_magnitude(self):
        _, line1_y = create_line_func(2.0, 3.0)
        _, line2_y = create_line_func(2.0, 10.0)
        magnitude_penalty_1 = magnitude_estimation.make_magnitude_penalty(line1_y)
        magnitude_penalty_2 = magnitude_estimation.make_magnitude_penalty(line2_y)
        assert magnitude_penalty_2 > magnitude_penalty_1

    def test_change_magnitude(self):
        line1_x, line1_y = create_line_func(2.0, 3.0)
        change_magnitude_1 = magnitude_estimation.make_avg_derivative_magnitude_estimation(line1_x, line1_y)

        line2_x, line2_y = create_line_func(2.0, 10.0)
        change_magnitude_2 = magnitude_estimation.make_avg_derivative_magnitude_estimation(line2_x, line2_y)
        assert common_tools.nearly_equal(change_magnitude_1, change_magnitude_2)

        line3_x, line3_y = create_line_func(4.0, 3.0)
        change_magnitude_3 = magnitude_estimation.make_avg_derivative_magnitude_estimation(line3_x, line3_y)
        assert change_magnitude_3 > change_magnitude_1

    def test_change_sign(self):
        _, increasing_line_y = create_line_func(2.0, 3.0)
        increase_estim = increase_estimation.make_increase_estimation(increasing_line_y)

        _, const_line_y = create_line_func(0.0, 3.0)
        const_estim = increase_estimation.make_increase_estimation(const_line_y)
        assert increase_estim > const_estim

        _, decreasing_line_y = create_line_func(-2.0, 3.0)
        decreasing_estim = increase_estimation.make_increase_estimation(decreasing_line_y)
        assert const_estim > decreasing_estim


if __name__ == '__main__':
    unittest.main()