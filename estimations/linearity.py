import common_tools as ct
import numpy as np
from scipy.interpolate import UnivariateSpline


def make_linearity_estimation(param, unknown_component_points, dbg_figname=None):
    table_X, table_Y = param, unknown_component_points
    domain = np.min(table_X), np.max(table_X)
    min_y, max_y = np.min(table_Y), np.max(table_Y)
    if min_y == max_y:
        return 1.0

    # todo: x already in [0, 1]
    Y_normalized = [(y - min_y) / (max_y - min_y) for y in table_Y]


    if dbg_figname is not None:
        import matplotlib.pyplot as plt

        plt.plot(table_X, Y_normalized)
        plt.savefig('plot_dump/{}.png'.format(dbg_figname))
        plt.close()
        with open('plot_dump/{}.txt'.format(dbg_figname), 'w') as ys_log:
            for y in Y_normalized:
                print(y, file=ys_log)

    spline = UnivariateSpline(table_X, Y_normalized, k=4, s=0)

    segment_count = 20
    step = 1.0 / segment_count
    segment_center_xs = [domain[0] + (domain[1] - domain[0]) * (step * i + step * 0.5) for i in range(segment_count)]
    segment_center_xs = [ct.clamp(domain[0], domain[1], x) for x in segment_center_xs]
    assert len(segment_center_xs) == segment_count

    segment_center_ys = [spline(x) for x in segment_center_xs]

    segment_corner_xs = [domain[0] + (domain[1] - domain[0]) * (step * i) for i in range(segment_count + 1)]
    segment_corner_ys = [spline(x) for x in segment_corner_xs]
    assert len(segment_corner_xs) == segment_count + 1

    segments_linearity = []
    for i in range(segment_count):
        segment_center_pt = np.array([segment_center_xs[i], segment_center_ys[i]], dtype=np.float128)

        segment_left_pt = np.array((segment_corner_xs[i], segment_corner_ys[i]), dtype=np.float128)
        segment_right_pt = np.array((segment_corner_xs[i+1], segment_corner_ys[i+1]), dtype=np.float128)

        segment_left_dir = segment_left_pt - segment_center_pt
        segment_left_dir /= np.linalg.norm(segment_left_dir)

        segment_right_dir = segment_right_pt - segment_center_pt
        segment_right_dir /= np.linalg.norm(segment_right_dir)

        angle_cos = np.dot(segment_left_dir, segment_right_dir)
        segment_linearity = 0.5 - angle_cos*0.5
        segments_linearity.append(segment_linearity)

    total_linearity = sum(segments_linearity) / segment_count

    return total_linearity