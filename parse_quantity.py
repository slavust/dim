import sympy
from enum import Enum
import re
from collections import OrderedDict


class MultiplicationParser(object):
    class ParseState(Enum):
        unit = 0
        unit_power = 1

    def __init__(self, str_expr):
        self.units = []
        self.str_expr = str_expr

        self.cur_state = self.ParseState.unit
        self.__reset_current_unit()
        self.__parse_mul()

    def get_units_with_powers(self):
        return self.units

    def __add_unit(self, name, power):
        if name == '':
            raise Exception("Empty unit name while parsing '{}'".format(self.str_expr))
        if name[0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
            raise Exception("Unit names starting with digits are not allowed (while parsing '{}')".format(self.str_expr))
        power_rational = sympy.Rational(power[0], power[1])
        if power_rational == sympy.nan:
            raise Exception("Unexpected power value (while parsing '{}')".format(self.str_expr))
        self.units.append((name, power_rational))

    def __reset_current_unit(self):
        self.cur_unit = ''
        self.cur_unit_power = [None, None]
        self.cur_unit_power_signs = [1, 1]
        self.cur_unit_power_index = 0

    def __switch_state(self, state):
        if state == self.ParseState.unit:
            if not self.cur_unit == '':
                # set numerator and denumerator of power to 1 if they were not specified
                powers = [1 if p is None else p for p in self.cur_unit_power]
                result_power = [sign * power for sign, power in zip(powers, self.cur_unit_power_signs)]
                self.__add_unit(self.cur_unit, result_power)
            self.__reset_current_unit()
        self.cur_state = state

    def __parse_mul(self):
        for ch in self.str_expr:
            if ch in ' \t':
                continue
            if self.cur_state == self.ParseState.unit:
                if ch == '^':
                    self.__switch_state(self.ParseState.unit_power)
                elif ch == '*':
                    self.__switch_state(self.ParseState.unit)
                else:
                    self.cur_unit += ch
            elif self.cur_state == self.ParseState.unit_power:
                if ch == '-':
                    if not self.cur_unit_power[self.cur_unit_power_index] is None:
                        raise Exception("Unexpected '-' in {}".format(self.str_expr))
                    self.cur_unit_power_signs[self.cur_unit_power_index] = -1
                elif ch == '/':
                    if self.cur_unit_power_index != 0:
                        raise Exception('Only one denominator is allowed (while parsing {})'.format(self.str_expr))
                    self.cur_unit_power_index = 1
                elif ch in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
                    ch_int = int(ch)
                    if self.cur_unit_power[self.cur_unit_power_index] is None:
                        self.cur_unit_power[self.cur_unit_power_index] = ch_int
                    else:
                        self.cur_unit_power[self.cur_unit_power_index] = \
                            self.cur_unit_power[self.cur_unit_power_index] * 10 + ch_int
                elif ch == '*':
                    self.__switch_state(self.ParseState.unit)
        self.__switch_state(self.ParseState.unit)


class QuantityParser(object):
    def __init__(self, str_expr):
        self.units_and_powers = OrderedDict()
        self.quantity_name = None

        self.__parse_quantity_expr(str_expr)

    def get_units_and_powers(self):
        return self.units_and_powers

    def get_quantity_name(self):
        return self.quantity_name

    def __parse_quantity_expr(self, quantity_expr):
        pattern = r'[ \t\r\n]*([a-zA-Z\\][a-zA-Z0-9_]*)(\[([^\]]+)\])?'
        match = re.match(pattern, quantity_expr)
        if match is None:
            raise ValueError('Unable to parse expression "{}"'.format(quantity_expr))
        groups = match.groups()
        if len(groups) != 1 and len(groups) != 3:
            raise ValueError('Unable to parse expression "{}"'.format(quantity_expr))
        self.quantity_name = groups[0]
        if len(groups) == 3:
            units_str = groups[2]
            self.__parse_units(units_str)

    def __add_units_mul(self, powers_sign, units_with_powers):
        powers = [(unit, powers_sign * power) for unit, power in units_with_powers]
        for unit, power in powers:
            if unit in self.units_and_powers:
                self.units_and_powers[unit] *= power
            else:
                self.units_and_powers[unit] = power

    def __parse_units(self, fraction_str):
        if fraction_str == '':
            raise Exception("Empty fraction (while parsing '{}')".format(fraction_str))
        multiplies = fraction_str.split('//')
        if len(multiplies) > 2:
            raise Exception(
                "Only one fraction division is allowed (while parsing '{}')".format(fraction_str))
        numerator_parser = MultiplicationParser(multiplies[0])
        self.__add_units_mul(1, numerator_parser.get_units_with_powers())
        if len(multiplies) == 2:
            denominator_parser = MultiplicationParser(multiplies[1])
            self.__add_units_mul(-1, denominator_parser.get_units_with_powers())


if __name__ == '__main__':
    expr_str = 'kg*m^-3*s^2/3//a^14*b^2/-3*c^1'
    parser = QuantityParser(expr_str)
    result = parser.get_units_and_powers()
    print(result)