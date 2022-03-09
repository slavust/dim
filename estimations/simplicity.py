from common_tools import power_cost


def make_simplicity_estimation(powers_list):
    power_costs = [power_cost(power) for power in powers_list]
    total_cost = sum(power_costs)
    return float(total_cost)
