import os

import click
import datasheets
import numpy as np
import pandas as pd
from pulp import LpVariable, LpProblem, LpMaximize, lpSum, PULP_CBC_CMD
import yaml


class Optimizer:

    def __init__(self, input_data, num_screens, budget):
        self.input_data = input_data
        self.num_screens = num_screens
        self.budget = budget
        self.movie_counts = None
        self.problem = None

    def create_vars(self):
        """Define the optimization decision variables"""
        self.movie_counts = {}
        for _, row in self.input_data.iterrows():
            var = LpVariable(f'{row.movie}_counts', cat='Integer',
                             lowBound=0, upBound=self.num_screens)
            self.movie_counts[row.movie] = var

    def get_objective_function(self, solved=False):
        objective = []
        for _, row in self.input_data.iterrows():
            val = _get_val(self.movie_counts[row.movie], solved)
            objective.append(val * row.revenue)
        return lpSum(objective) if solved else np.sum(objective)

    def get_constraints(self):
        constraints = []
        constraint = (
            lpSum(self.movie_counts.values()) == self.num_screens,
            'every screen must be assigned'
        )
        constraints.append(constraint)

        total_cost = []
        for _, row in self.input_data.iterrows():
            total_cost.append(self.movie_counts[row.movie] * row.cost)

        constraint = lpSum(total_cost) <= self.budget, 'Limited budget'
        constraints.append(constraint)

        return constraints

    def get_solution(self, solved):
        """Generate a string that contains the solution information"""
        msg = []
        if solved:
            objective_value = self.get_objective_function(solved)
            msg.append(f'Optimization successful! '
                       f'Total Revenue = {objective_value}')
            for _, row in self.input_data.iterrows():
                val = self.movie_counts[row.movie].varValue
                if row.movie == 'empty':
                    msg.append(f'Leave {int(val)} screens empty')
                else:
                    msg.append(f'Movie {row.movie} is on {int(val)} screens')
        else:
            msg.append('Optimization algorithm failed!')
        return '\n'.join([x for x in msg])

    def build_allocation(self):
        movie = []
        num_screens = []
        cost = []
        revenue = []

        for _, row in self.input_data.iterrows():
            val = self.movie_counts[row.movie].varValue
            movie.append(row.movie)
            num_screens.append(val)
            cost.append(row.cost * val)
            revenue.append(row.revenue * val)

        df = pd.DataFrame({'movie': movie, 'num_screens': num_screens,
                           'revenue': revenue, 'cost': cost})
        total_revenue = df.revenue.sum()
        total_cost = df.cost.sum()
        total_screens = df.num_screens.sum()
        last_row = pd.DataFrame(
            {'movie': ['total'], 'num_screens': [total_screens],
             'revenue': [total_revenue], 'cost': [total_cost]})
        df = pd.concat([df, last_row], axis=0)
        df = df.set_index('movie', drop=True)
        return df

    def run(self):
        self.problem = LpProblem('FML', LpMaximize)
        self.create_vars()
        self.problem += self.get_objective_function(solved=False)
        for constraint in self.get_constraints():
            self.problem += constraint
        status = self.problem.solve(PULP_CBC_CMD(msg=3))
        solved = status == 1
        return solved


def _get_val(var, solved):
    return var.varValue if solved else var


def parse_conf(conf):
    with open(conf, 'r') as f:
        conf = yaml.load(f)

    os.environ['DATASHEETS_SECRETS_PATH'] = conf['creds_file']
    os.environ['DATASHEETS_SERVICE_PATH'] = conf['service_file']

    workbook = conf['workbook']
    num_screens = conf['num_screens']
    empty_screen_cost = conf['empty_screen_cost']
    budget = conf['budget']

    return workbook, num_screens, empty_screen_cost, budget


def load_data(workbook):
    tab = workbook.fetch_tab('inputs')
    return tab.fetch_data()


def run_pipeline(conf='conf.yml'):
    """
    Pull inputs from google sheets, solve the allocation problem, and write the
    solution back to the sheet.
    """
    workbook, num_screens, empty_screen_cost, budget = parse_conf(conf)

    # Pull data
    client = datasheets.Client(service=True)
    workbook = client.fetch_workbook(workbook)
    input_data = load_data(workbook)

    empty_screen = pd.DataFrame({'movie': ['empty'], 'revenue': [0],
                                 'cost': [empty_screen_cost]})
    input_data = pd.concat([input_data, empty_screen], axis=0)

    # Define and solve allocation problem
    optimizer = Optimizer(input_data, num_screens, budget)
    solved = optimizer.run()
    solution_msg = optimizer.get_solution(solved)
    print(solution_msg)
    if solved:
        # Write the results to google sheet.
        allocation = optimizer.build_allocation()
        tab = workbook.fetch_tab('outputs')
        tab.insert_data(allocation)
    return solution_msg


@click.command()
@click.option('--conf', default='conf.yml')
def main(conf):
    run_pipeline(conf)


if __name__ == '__main__':
    main()
