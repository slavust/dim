import common_tools as ct
import numpy as np
from scipy.interpolate import UnivariateSpline


def are_function_segments_equal(function, segment1_domain, segment2_domain, accuracy):
    point_count = int(1.0/accuracy + 1)
    xs1 = [segment1_domain[0] + (segment1_domain[1] - segment1_domain[0]) * accuracy * i for i in range(point_count)]
    xs1 = [ct.clamp(segment1_domain[0], segment1_domain[1], x) for x in xs1]
    ys1 = [function(x) for x in xs1]

    xs2 = [segment2_domain[0] + (segment2_domain[1] - segment2_domain[0]) * accuracy * i for i in range(point_count)]
    xs2 = [ct.clamp(segment2_domain[0], segment2_domain[1], x) for x in xs2]
    ys2 = [function(x) for x in xs2]

    for y1, y2 in zip(ys1, ys2):
        equal = abs(y1 - y2) <= accuracy
        if not equal:
            return False
    return True


def split_domain_on_segments(domain, segment_length, accuracy):
    '''
    разбивает область определения функции на сегменты
    длиной segment_length (+ остаточный последний сегмент, если он длинее точности)
    '''
    domain_length = domain[1] - domain[0]
    full_segment_count = int(domain_length / segment_length)

    segment_starts = [domain[0] + segment_length * i for i in range(full_segment_count)]
    segment_ends = [domain[0] + segment_length * (i + 1) for i in range(full_segment_count)]

    last_segment_start = segment_ends[-1]  # должен совпадать с концом предыдущего сегмента
    last_segment_end = domain[1]  # идёт до конца области определения
    last_segment_length = last_segment_end - last_segment_start
    if last_segment_length > accuracy:
        segment_starts.append(last_segment_start)
        segment_ends.append(last_segment_end)

    segments_domains = list(zip(segment_starts, segment_ends))
    return segments_domains


def make_periodicity_estimation(table_X, table_Y, dbg_figname=None):
    '''
    взять стартовую точку
    найти все y совпадающие с данной в пределах точности
    сравнивать период начинающийся с первой точки с периодои, начинающимся с 2, затем с 3
    (если точка совпадает с экстремумом, то и следующая по очереди может быть началом периода)
    как сравнивать два периода:
        * составить список точек одинакового количества в каждом предполагаемом периоде
        * сравнивать поточечно в пределах точности
    если 2 сравниваемых периода совпало, необходимо проверить все вмещающиеся в область определения периоды
    (включая возможно незавершенный период в конце области определения)
    если периоды совпали: оценка периодичности = 1 - accuracy
    '''
    domain = np.min(table_X), np.max(table_X)
    min_y, max_y = np.min(table_Y), np.max(table_Y)
    if min_y == max_y:
        return 1.0

    Y_normalized = [(y - min_y) / (max_y - min_y) for y in table_Y] # todo: x already in [0, 1]

    if dbg_figname is not None:
        import matplotlib.pyplot as plt

        plt.plot(table_X, Y_normalized)
        plt.savefig('plot_dump/{}.png'.format(dbg_figname))
        plt.close()
        with open('plot_dump/{}.txt'.format(dbg_figname), 'w') as ys_log:
            for y in Y_normalized:
                print(y, file=ys_log)

    spline = UnivariateSpline(table_X, Y_normalized, k=4, s=0)

    step = 0.01
    accuracy = 0.0
    periodicity_found = False
    while (not periodicity_found) and accuracy < 1.0:
        accuracy += step
        point_count = int(1.0 / accuracy + 1)
        xs = [domain[0] + (domain[1]-domain[0]) * accuracy * i for i in range(point_count)]
        xs = [ct.clamp(domain[0], domain[1], x) for x in xs]
        ys = [spline(x) for x in xs]
        control_x = xs[0]
        control_y = ys[0]
        similar_y_indices = list(filter(lambda i: abs(ys[i] - control_y) <= accuracy, range(1, point_count)))
        for indx in similar_y_indices:
            segment_x_length = xs[indx] - control_x
            segments_domains = split_domain_on_segments(domain, segment_x_length, accuracy)
            control_segment = segments_domains[0]
            compared_segments = segments_domains[1:]
            segments_equality = [are_function_segments_equal(spline, control_segment, segment_i, accuracy)
                                 for segment_i in compared_segments]
            if all(segments_equality):
                periodicity_found = True
                break
    if not periodicity_found:
        return 0.0
    return ct.clamp(0.0, 1.0, 1.0 - accuracy)
