import pylatex as pl
from sympy import fraction
import os.path
import urllib.parse


def gen_latex_formula(quantity_names, powers):
    positive_powers = [i for i in range(len(powers)) if powers[i] > 0]
    negative_powers = [i for i in range(len(powers)) if powers[i] < 0]

    def quantity_with_power_to_latex(name, power):
        numerator, denominator = fraction(power)
        assert numerator != 0
        # negative powers are processed separately
        numerator, denumerator = abs(numerator), abs(denominator)
        quant_latex = name
        if numerator != 1:
            quant_latex = quant_latex + '^{' + str(numerator) + '}'
        if denumerator != 1:
            quant_latex = '\\sqrt{' + quant_latex + '}'
        return quant_latex

    numerator = ''
    if len(positive_powers) == 0:
        numerator = '1'
    else:
        positive_quantities_wth_powers = [(quantity_names[indx], powers[indx]) for indx in positive_powers]
        numerator = ' '.join([quantity_with_power_to_latex(*quant_and_pow)
                             for quant_and_pow in positive_quantities_wth_powers])
    formula_latex = numerator

    if len(negative_powers) != 0:
        negative_quantities_wth_powers = [(quantity_names[indx], powers[indx]) for indx in negative_powers]
        denominator = ' '.join([quantity_with_power_to_latex(*quant_and_pow)
                                for quant_and_pow in negative_quantities_wth_powers])
        formula_latex = '$\\frac{' + formula_latex + '}{' + denominator + '}$'
        domain = 'https://approach0.xyz/search/?q='
        query = urllib.parse.quote(formula_latex)
        formula_with_href = pl.NoEscape('\\href{' + domain + query + '}{' + formula_latex + '}')

    return formula_with_href


def print_report(report_table, columns_ordered, quantity_names_ordered, out_path):
    doc = pl.Document()
    doc.documentclass = pl.Command(
        'documentclass',
        options=['landscape', 'a4paper','oneside', 'legno', 'notitlepage'],
        arguments=['report'])
    #doc.packages.append(pl.Package('hyperref'))
    doc.packages.append(pl.Package('hyperref', options=['hidelinks',
                                                        'colorlinks=true',
                                                        'linkcolor=blue',
                                                        'urlcolor=blue',
                                                        'citecolor=blue',
                                                        'anchorcolor=blue']))
    doc.packages.append(pl.Package('geometry', options=['margin=0.5 in']))

    full_columns = ('N',) + tuple(columns_ordered)  # + ('Unknown component', )
    formats = ['l']*len(full_columns)
    formats[columns_ordered.index('formula')+1] = 'p{2cm}'

    with doc.create(pl.Section('Summaries')):
        with doc.create(pl.LongTable(' '.join(formats))) as summaries_table:
            summaries_table.add_hline()
            summaries_table.add_row(full_columns)
            summaries_table.add_hline()
            summaries_table.end_table_header()
            summaries_table.add_hline()
            summaries_table.add_row((pl.MultiColumn(len(full_columns), align='r',
                                     data='Containued on Next Page'),))
            summaries_table.add_hline()
            summaries_table.end_table_footer()
            summaries_table.add_hline()
            summaries_table.add_row((pl.MultiColumn(len(full_columns), align='r',
                                     data='Not Containued on Next Page'),))
            summaries_table.add_hline()
            summaries_table.end_table_last_footer()

            for row_indx, row in enumerate(report_table):
                row_ordered = ['{0:.3f}'.format(row[col_name]) if col_name != 'formula'
                               else gen_latex_formula(quantity_names_ordered, row[col_name])
                               for col_name in columns_ordered]
                #formula_indx = columns_ordered.index('formula')
                #formula_powers = row_ordered[formula_indx]
                #formula_latex = gen_latex_formula(quantity_names_ordered, formula_powers)
                #row_ordered[formula_indx] = pl.Math(data=[pl.NoEscape(formula_latex)], inline=True)

                row_ordered = [row_indx + 1] + row_ordered
                summaries_table.add_row(row_ordered)

    path_and_ext = os.path.splitext(out_path)
    if len(path_and_ext) != 2:
        raise ValueError('Wrong output path: "{}"'.format(out_path))
    ext = path_and_ext[1].lower()
    if ext != '.pdf':
        raise ValueError('Only pdf files are supported')

    doc.generate_pdf(out_path)
    doc.generate_tex(out_path + '.tex')
