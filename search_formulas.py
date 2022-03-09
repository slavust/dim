import sympy as sp


class DimensionalFormulaSearch(object):
    @staticmethod
    def find_powers_equations(required_quantity_units, influencing_quantities_units):
        num_rows = len(influencing_quantities_units)
        assert num_rows > 0
        num_cols = len(influencing_quantities_units[0])
        assert num_rows > 0
        assert num_cols == len(required_quantity_units)

        # solve linear equation system to find applicable powers of quantities
        unit_matrix = sp.Matrix(influencing_quantities_units)
        quantities_pow_variables = sp.Matrix(1, num_rows, sp.symbols('x0:{}'.format(num_rows)))
        right_eq_side = sp.Matrix(1, num_cols, required_quantity_units)
        eq = list(quantities_pow_variables * unit_matrix - right_eq_side)
        quantities_pow_variables = list(quantities_pow_variables)

        solutions = sp.solve(eq, quantities_pow_variables, set=True)
        if len(solutions) == 0:
            raise ValueError('Required units cannot be derived from given quantities')
        dependent_variables = tuple(solutions[0])
        assert len(solutions[1])==1
        solution = list(solutions[1])[0]

        independent_variables = tuple([variable for variable in quantities_pow_variables
                                 if variable not in dependent_variables])
        return dependent_variables, independent_variables, solution, quantities_pow_variables

    @staticmethod
    def generate_powers_for_weight(power_weight):
        if power_weight == 0:
            return (0,),
        elif power_weight == 1:
            return (1,), (-1,)

        powers = []
        numerator = power_weight
        denumerator = 1
        end = numerator + 1
        while denumerator != end:
            power = sp.Rational(numerator, denumerator)
            result_numerator = sp.fraction(power)[0]
            # ones and other reduced fractions
            if result_numerator != numerator:
                numerator -= 1
                denumerator += 1
                continue
            powers.extend([(power,), (-power,)])
            numerator -= 1
            denumerator += 1
        return tuple(powers)

    @staticmethod
    def generate_powers_for_n_independent_quantities(independent_quantity_count, power_weight):
        #todo: debug
        def recursive_power_list_generation(left_weight, quantity_count):
            if quantity_count == 1:
                return DimensionalFormulaSearch.generate_powers_for_weight(left_weight)
            if left_weight == 0:
                return (0,)*quantity_count,
            result_grid = []
            for i in range(left_weight+1):
                cur_quantity_powers = DimensionalFormulaSearch.generate_powers_for_weight(i)
                next_quantities_powers = recursive_power_list_generation(left_weight-i, quantity_count-1)
                cur_grid = [cur_quantity_pow + next_quantity_pow for cur_quantity_pow in cur_quantity_powers
                               for next_quantity_pow in next_quantities_powers]
                result_grid.extend(cur_grid)
            return tuple(result_grid)

        independent_power_grid = recursive_power_list_generation(power_weight, independent_quantity_count)
        return independent_power_grid

    @staticmethod
    def power_cost(x):
        n, d = sp.fraction(sp.Rational(x))
        return abs(n) + abs(d)

    @staticmethod
    def power_set_cost(power_set):
        return sum([DimensionalFormulaSearch.power_cost(power) for power in power_set])

    @staticmethod
    def generate_quantities_powers_multiplies(max_formulas, max_downcycles, required_units, quantities_units):
        dependent_power_variables, independent_power_variables, dependent_powers_equations, all_power_vars_ordered = \
            DimensionalFormulaSearch.find_powers_equations(required_units, quantities_units)

        if len(independent_power_variables) == 0:
            exact_solution = []
            for var in all_power_vars_ordered:
                var_solution = dependent_powers_equations[var]
                assert var_solution.is_number
                exact_solution.append(var_solution)
            return [tuple(exact_solution)]

        independent_power_count = len(independent_power_variables)

        found_formulas = []

        downcycle_count = -1
        current_weight = 0
        future_powers = dict()
        while len(found_formulas) < max_formulas and downcycle_count < max_downcycles:
            found_formula = False
            generated_independent_powers = DimensionalFormulaSearch.generate_powers_for_n_independent_quantities(
                independent_power_count,
                current_weight)
            for generated_indep_pows in generated_independent_powers:
                assert len(generated_indep_pows) == independent_power_count
                indep_powers_by_vars ={indep_pow_var: power
                                            for indep_pow_var, power
                                            in zip(independent_power_variables, generated_indep_pows)}
                dependent_powers_by_vars = {power: power_equation.subs(indep_powers_by_vars)
                                              for power, power_equation
                                            in zip(dependent_power_variables, dependent_powers_equations)}
                all_powers_by_vars = {**indep_powers_by_vars, **dependent_powers_by_vars}
                all_powers_ordered = tuple(all_powers_by_vars[var] for var in all_power_vars_ordered)

                formula_cost = DimensionalFormulaSearch.power_set_cost(all_powers_ordered)
                assert formula_cost >= current_weight
                if formula_cost > current_weight:
                    if formula_cost in future_powers.keys():
                        future_powers[formula_cost].append(all_powers_ordered)
                    else:
                        future_powers[formula_cost] = [all_powers_ordered]
                else:
                    found_formula = True
                    found_formulas.append(all_powers_ordered)

            if current_weight in future_powers.keys():
                assert DimensionalFormulaSearch.power_set_cost(future_powers[current_weight][0]) == current_weight
                found_formulas.extend(future_powers[current_weight])
                del future_powers[current_weight]
                found_formula = True

            if found_formula:
                downcycle_count = 0
            else:
                downcycle_count += 1
            current_weight += 1

        return found_formulas
