import csv
from collections import OrderedDict
import parse_quantity

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