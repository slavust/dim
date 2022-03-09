#!/usr/bin/python3

import argparse
import csv
from copy import deepcopy
from collections import OrderedDict

import parse_quantity
from search_formulas import DimensionalFormulaSearch
import estimate_formulas
import report_printing
import gooey

class DimensionalFormulaSearchCli(object):
    @staticmethod
    def load_measurements_csv(csv_path):
        quantities = OrderedDict()
        quantities_by_column_indices = OrderedDict()
        not_measured_quantities = list()
        with open(csv_path, 'r', newline='') as csv_file:
            csv_table = csv.reader(csv_file, dialect='excel') # libreoffice allows to choose dialect
            # TODO: fix
            #if len(csv_table) < 2:
            #    raise ValueError('Specified csv table has no required data')
            csv_table = list(csv_table)
            quantities_row = csv_table[0]
            for col_indx, quantity_str in enumerate(quantities_row):
                quantity_parser = parse_quantity.QuantityParser(quantity_str)
                quantity_name = quantity_parser.get_quantity_name()
                if quantity_name in quantities.keys():
                    raise ValueError('Quantity named "{}" specified twice in file "{}"'
                                     .format(quantity_name, csv_path))
                quantity_data = OrderedDict()
                quantity_units = quantity_parser.get_units_and_powers()
                if quantity_units is not None:
                    quantity_data['units'] = quantity_units
                quantities[quantity_name] = quantity_data
                quantities_by_column_indices[col_indx] = quantity_name

            first_measurements_row = csv_table[1]
            for col_indx, csv_col in enumerate(first_measurements_row):
                if col_indx not in quantities_by_column_indices.keys():
                    raise ValueError('Unable to parse "{}" file: different number of columns in rows'
                                     .format(csv_file))
                if len(csv_col) == 0:
                    not_measured_quantities.append(col_indx)
                    continue
                quantities[quantities_by_column_indices[col_indx]]['measurements'] = []

            for row_indx, csv_row in zip(range(2, len(csv_table) - 2), csv_table[2:]):
                for col_indx, csv_col in enumerate(csv_row):
                    if col_indx not in quantities_by_column_indices.keys():
                        raise ValueError('Unable to parse "{}" file: different number of '
                                         'columns in rows'.format(csv_file))
                    if len(csv_col) == 0:
                        if col_indx not in not_measured_quantities:
                            raise ValueError(
                                'Unable to parse "{}" file: quantity measurements'
                                ' are expected to be fully specified or fully unspecified'
                                .format(csv_path))
                        continue
                    if col_indx in not_measured_quantities:
                        raise ValueError(
                            'Unable to parse "{}" file: quantity measurements '
                            'are expected to be fully specified or fully unspecified'
                            .format(csv_path))
                    quantities[quantities_by_column_indices[col_indx]]['measurements']\
                        .append(float(csv_col))
            return quantities

    @staticmethod
    def make_quantities_base_units_vectors(quantities_table):
        from sympy import Rational

        all_base_unit_names = set()
        for quantity_data in quantities_table.values():
            if 'units' not in quantity_data.keys():
                continue
            all_base_unit_names |= set(quantity_data['units'].keys())
        all_base_unit_names = sorted(list(all_base_unit_names))

        quantities_base_unit_vectors = OrderedDict()
        for quantity_name, quantity_data \
                in zip(quantities_table.keys(), quantities_table.values()):
            if 'units' not in quantity_data.keys():
                quantities_base_unit_vectors[quantity_name] = (0,)*len(all_base_unit_names)
                continue
            units_vector = []
            for unit_name in all_base_unit_names:
                if unit_name not in quantity_data['units']:
                    units_vector.append(Rational(0))
                else:
                    units_vector.append(quantity_data['units'][unit_name])
            quantities_base_unit_vectors[quantity_name] = tuple(units_vector)

        return quantities_base_unit_vectors, all_base_unit_names

    @staticmethod
    def prepare_report_table(
            formulas,
            formula_estims,
            simplicity_weight,
            magnitude_weight,
            linearity_weight,
            periodicity_weight,
            monotonicity_weight,
            change_magnitude_weight,
            change_sign_weight):
        report_table = list()
        for formula, estim_row in zip(formulas, formula_estims):
            if 'invalid' in estim_row:
                continue
            report_row = deepcopy(estim_row)
            report_row['simplicity'] = simplicity_weight * report_row['simplicity']
            report_row['magnitude'] = magnitude_weight * report_row['magnitude']
            report_row['linearity'] = linearity_weight * report_row['linearity']
            report_row['periodicity'] = periodicity_weight * report_row['periodicity']
            report_row['monotonicity'] = monotonicity_weight * report_row['monotonicity']
            report_row['change magnitude'] = change_magnitude_weight * report_row['change magnitude']
            report_row['change sign'] = change_sign_weight * report_row['change sign']
            report_row['total'] = report_row['simplicity'] \
                                  + report_row['magnitude'] \
                                  + report_row['linearity'] \
                                  + report_row['periodicity'] \
                                  + report_row['monotonicity'] \
                                  + report_row['change magnitude'] \
                                  + report_row['change sign']
            report_row['formula'] = formula
            report_table.append(report_row)
        report_table.sort(key=lambda formula_row: formula_row['total'], reverse=True)
        return report_table

    @staticmethod
    @gooey.Gooey(program_name='Dim',
                 program_description='Tries to guess right equation by using dimentional analysis, available measurements and some unknown component heuristics',
                 tabbed_groups=True)
    def main():
        DEFAULT_MAX_FORMULAS = 20
        DEFAULT_MAX_CYCLES = 40

        parser = gooey.GooeyParser()
        equations_search = parser.add_argument_group('Search equations parameters')
        equations_search.add_argument('-f', '--max-formulas', type=int, default=DEFAULT_MAX_FORMULAS,
                            help='Max formula count to search')
        equations_search.add_argument('--max-downcycles', type=int, default=DEFAULT_MAX_CYCLES,
                            help='Max number of cycles performed to '
                                 'search new formula without success')
        equations = parser.add_argument_group('Equation heuristics')
        equations.add_argument('-s', '--simplicity-weight', type=float, default=0.0,
                            help='Weight of formula simplicity '
                                 'during prioritization')
        unknown_heuristics = parser.add_argument_group('Unknown component heuristics')
        magnitude = unknown_heuristics.add_argument_group('Unknown component magnitude heuristics')
        magnitude.add_argument('-m', '--magnitude-weight', type=float, default=0.0,
                            help='Weight of formula magnitude during prioritization')
        magnitude.add_argument('-M', '--magnitude-greater-better', choices=['yes', 'no'],
                            default='yes',
                            help='Prefere greater magnitude during formula prioritization')
        unknown_heuristics.add_argument('-l', '--linearity-weight', type=float, default=0.0,
                            help='Weight of formula linearity during prioritization')
        unknown_heuristics.add_argument('-p', '--periodicity-weight', type=float, default=0.0,
                            help='Weight of formula periodicity during prioritization')
        derivative = unknown_heuristics.add_argument_group('Unknown component derivative heuristics')
        derivative.add_argument('-g', '--change-sign-weight', type=float, default=0.0,
                            help='Weight of the fact of increasing or decreasing')
        derivative.add_argument('-i', '--increase-is-better', choices=['yes', 'no'],
                            default='yes',
                            help='Prefer increase over decrease')
        derivative.add_argument('-c', '--change-magnitude-weight', type=float, default=0.0,
                            help='Weight of change magnitude during prioritization')
        derivative.add_argument('-C', '--change-greater-better',
                            choices=['yes', 'no'],
                            default='yes',
                            help='Treat greater change magnitude as better')
        unknown_heuristics.add_argument('-n', '--monotonicity-weight', type=float, default=0.0,
                            help='Weight of monotonicity during prioritization')
        parser.add_argument('input_csv', type=str,
                            help='Path to input csv file', widget='FileChooser')
        parser.add_argument('searched_quantity', type=str,
                            help='Searched quantity name '
                                 '(should correspond to quantity name in csv)')
        parser.add_argument('out_file', type=str,
                            help='Path to output file', widget='FileSaver')

        args = parser.parse_args()

        quantities_table = DimensionalFormulaSearchCli.load_measurements_csv(args.input_csv)

        required_quantity_name = args.searched_quantity
        all_quantity_names = sorted(list(set(quantities_table.keys())))
        if required_quantity_name not in all_quantity_names:
            raise ValueError('Searched quantity "{}" is not present in "{}" table'.format(
                required_quantity_name,
                args.input_csv))
        influencing_quantity_names_ordered = \
            sorted(list(set(all_quantity_names) - {required_quantity_name}))
        if len(influencing_quantity_names_ordered) == 0:
            raise ValueError('There should be more quantities in "{}"'.format(args.input_csv))

        quantities_base_unit_vectors, all_unit_names = \
            DimensionalFormulaSearchCli.make_quantities_base_units_vectors(quantities_table)
        required_quantity_units_vec = quantities_base_unit_vectors[required_quantity_name]
        influencing_quantities_units_matr = [quantities_base_unit_vectors[quantity_name]
                                             for quantity_name
                                             in influencing_quantity_names_ordered]

        formulas_represented_by_powers = \
            DimensionalFormulaSearch.generate_quantities_powers_multiplies(
                args.max_formulas,
                args.max_downcycles,
                required_quantity_units_vec,
                influencing_quantities_units_matr)

        formulas_estimations = estimate_formulas.make_formulas_estimation(
            formulas_represented_by_powers, quantities_table,
            required_quantity_name, influencing_quantity_names_ordered,
            args.magnitude_greater_better == 'yes',
            args.increase_is_better == 'yes',
            args.change_greater_better == 'yes')

        report_table = DimensionalFormulaSearchCli.prepare_report_table(
            formulas_represented_by_powers,
            formulas_estimations,
            args.simplicity_weight,
            args.magnitude_weight,
            args.linearity_weight,
            args.periodicity_weight,
            args.monotonicity_weight,
            args.change_magnitude_weight,
            args.change_sign_weight)

        report_printing.print_report(report_table,
                                     ('formula',
                                      'simplicity',
                                      'magnitude',
                                      'change magnitude',
                                      'change sign',
                                      'linearity',
                                      'periodicity',
                                      'monotonicity'),
                                     influencing_quantity_names_ordered,
                                     args.out_file)


if __name__ == '__main__':
    DimensionalFormulaSearchCli.main()

