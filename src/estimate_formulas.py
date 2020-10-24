#!/usr/bin/python3

import numpy as np

import linearity_estimation
import simplicity_estimation
import magnitude_estimation
import periodicity_estimation
import monotonicity_estimation
import increase_estimation
import common_tools as common


def make_formulas_estimation(formulas_list,
                             quantities_table,
                             required_quantity_name,
                             influencing_quantity_names_ordered,
                             magnitude_greater_is_better,
                             increase_is_better,
                             greater_change_is_better):
    """

    """
    # todo: make more convenient
    # find one quantity with measurements to determine table height
    table_height = None
    for quantity_data in quantities_table.values():
        if 'measurements' in quantity_data:
            table_height = len(quantity_data['measurements'])
            break
    assert table_height is not None

    #  move all quantities to one side of equations
    quantity_names_ordered = tuple(influencing_quantity_names_ordered) + (required_quantity_name, )
    formulas_list = [formula + (-1,) for formula in formulas_list]

    known_quantities_mask = ['measurements' in quantities_table[formula_name] for formula_name in quantity_names_ordered]
    measurements_only_table = np.transpose(np.array([quantities_table[quantity_name]['measurements']
                                        if 'measurements' in quantities_table[quantity_name]
                                        else [1.0]*table_height
                                        for quantity_name in quantity_names_ordered]))
    # todo: optionally load from csv?
    todo_param = np.arange(0.0, 1.0, 1.0/table_height)
    raw_formulas_estimations = []
    for formula in formulas_list:
        evaluated_unknown_component_points = eval_unknown_component_points(
            formula=formula,
            table=measurements_only_table,
            knowns_mask=known_quantities_mask)

        for i in range(len(evaluated_unknown_component_points)):
            if (np.isnan(evaluated_unknown_component_points[i])
                    or np.isinf(evaluated_unknown_component_points[i])
                    or np.isneginf(evaluated_unknown_component_points[i])):
                raw_formulas_estimations.append({'invalid': 'invalid in given measurements'})
                continue

        dbg_filename = [str(power).replace('/', '_') for power in formula]
        dbg_filename = '__'.join(dbg_filename)

        raw_simplicity_estim = simplicity_estimation.make_simplicity_estimation(formula)
        raw_magnitude_estim = magnitude_estimation.make_magnitude_penalty(evaluated_unknown_component_points)
        raw_change_estim = magnitude_estimation.make_avg_derivative_magnitude_estimation(
            todo_param,
            evaluated_unknown_component_points)
        raw_linearity_estim = linearity_estimation.make_linearity_estimation(
            todo_param,
            evaluated_unknown_component_points)
        raw_periodicity_estim = periodicity_estimation.make_periodicity_estimation(
            todo_param,
            evaluated_unknown_component_points)
        raw_monotonicity_estim = monotonicity_estimation.make_non_monothonicity_estimation(
            todo_param,
            evaluated_unknown_component_points)
        raw_increase_estim = increase_estimation.make_increase_estimation(evaluated_unknown_component_points)
        raw_formulas_estimations.append({
            'simplicity': raw_simplicity_estim,
            'magnitude': raw_magnitude_estim,
            'linearity': raw_linearity_estim,
            'periodicity': raw_periodicity_estim,
            'monotonicity': raw_monotonicity_estim,
            'change magnitude': raw_change_estim,
            'change sign': raw_increase_estim,
            'parameter_points': todo_param,
            'unknowns_points': evaluated_unknown_component_points}
        )

    normalized_estimations = raw_formulas_estimations
    common.normalize_80(normalized_estimations, 'simplicity', revert=True)
    common.normalize_80(normalized_estimations, 'magnitude', revert=not magnitude_greater_is_better)
    common.normalize_80(normalized_estimations, 'linearity', revert=False)
    common.normalize_80(normalized_estimations, 'periodicity', revert=False)
    common.normalize_80(normalized_estimations, 'monotonicity', revert=True)
    common.normalize_80(normalized_estimations, 'change magnitude', revert=not greater_change_is_better)
    common.normalize_80(normalized_estimations, 'change sign', revert=not increase_is_better)

    return normalized_estimations


def eval_unknown_component_points(formula,
                                  table,
                                  knowns_mask):
    # степени, в которые требуется возвести известные величины для получения произведения неизвестных
    # todo: когда лучше инвертировать степени? (на данный момент - когда неизвестна только искомая величина)
    all_unknowns_in_denominator = True
    for i, power in enumerate(formula):
        if not knowns_mask[i] and power > 0:
            all_unknowns_in_denominator = False
            break

    power_inverter = -1.0
    if all_unknowns_in_denominator:
        power_inverter = 1.0

    knowns_powers_inverse = np.array([power_inverter*float(base_unit_power) if known else 0.0
                             for base_unit_power, known in zip(formula, knowns_mask)])
    powed = np.power(table, knowns_powers_inverse)
    unknown_component_points = np.prod(powed, axis=-1)
    return unknown_component_points
