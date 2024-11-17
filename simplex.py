import copy

import numpy as np
import plotly.graph_objects as go


class SimplexMethod:
    def __init__(self, constraints, function):
        self.n = len(constraints)
        self.m = 3
        self.function = function
        self.row = ['x1', 'x2', '-b']
        self.column = ['y' + str(_) for _ in range(1, self.n + 1)]
        self.column.append('c')

        # add constraints
        self.table = [constraint for constraint in constraints]

        # add function
        self.table.append(function)
        self.table[-1].append(0)

    def print_table(self):
        print("\t", end='')
        print("\t".join(self.row))
        for row in range(self.n + 1):
            print(self.column[row], end='\t')
            print("\t".join([str(round(val, 6)) for val in self.table[row]]))

    def f(self, x1, x2):
        return self.function[0] * x1 + self.function[1] * x2

    def find_optimum(self) -> (float, float):
        def index_of(s):
            for row in range(len(self.column)):
                if self.column[row] == s:
                    return row
            return len(self.column)

        x1_i = index_of('x1')
        x2_i = index_of('x2')
        x1 = 0
        x2 = 0

        if x1_i != len(self.column):
            x1 = self.table[x1_i][-1]
        if x2_i != len(self.column):
            x2 = self.table[x2_i][-1]

        return x1, x2

    def pick_element(self) -> (bool, int, int, float):
        # find negative in `-b` column
        target_row = self.n
        for idx in range(self.n):
            if self.table[idx][-1] < 0:
                target_row = idx
                break

        # if no negative element in `-b` column then search negative in row `c`
        if target_row == self.n:
            target_column = self.m
            for idx in range(self.m - 1):
                if self.table[-1][idx] < 0:
                    target_column = idx
                    break

            # no negative element in `c` column, optimum already found
            if target_column == self.m:
                x1, x2 = self.find_optimum()
                return False, x1, x2, self.f(x1, x2)

            # otherwise find max negative num:
            # `m` where (-b_m) / (table[m][neg_index] -> max < 0
            target_row = self.n
            min_val = self.table[0][-1] / self.table[0][target_column]

            for row in range(self.n):
                if self.table[row][target_column] == 0:
                    continue
                val = self.table[row][-1] / self.table[row][target_column]

                if val == 0 and min_val > 0:
                    min_val = val
                    target_row = row
                    continue

                if val < 0 <= min_val:
                    min_val = val
                    target_row = row
                    continue

                if 0 > val > min_val:
                    min_val = val
                    target_row = row
                    continue
            if min_val > 0:
                raise "symplex method does not converge"
            return True, target_row, target_column, self.table[target_row][target_column]

        # find non-negative element in row
        target_column = self.m
        for column in range(self.m - 1):
            if self.table[target_row][column] > 0:
                target_column = column
                break

        # logic error?
        if target_column == self.m:
            raise "incorrect system?"

        return True, target_row, target_column, self.table[target_row][target_column]

    def recalculate_matrix(self):
        _is_successful, r, c, _ = sm.pick_element()

        if not is_successful:
            return

        new_table = copy.deepcopy(self.table)

        # swap variables
        self.row[c], self.column[r] = self.column[r], self.row[c]

        # step 1: divide row with picked element by `-e`
        for column in range(len(new_table[r])):
            new_table[r][column] /= -self.table[r][c]

        # step 2: divide column with picked element by `e`
        for row in range(len(new_table)):
            new_table[row][c] /= self.table[r][c]

        # step 3: inverse picked element
        new_table[r][c] = 1 / self.table[r][c]

        # step 4: recalculate matrix
        for row in range(len(new_table)):
            if row == r:
                continue
            for column in range(len(new_table[row])):
                if column == c:
                    continue

                new_table[row][column] = (
                        (self.table[row][column] * self.table[r][c] -
                         self.table[r][column] * self.table[row][c]) / self.table[r][c])

        # recalculate F(optimum)
        self.table = new_table
        new_table[-1][-1] = self.f(*self.find_optimum())


# Constraints such as
# y = a * x1 + b * x2 + c > 0
# c = grad F(x1,x2)
y1 = [1, 1, -2]
y2 = [-1, 1, 2]
y3 = [0, -1, 2]
c = [-1, 0]

sm = SimplexMethod([y1, y2, y3], c)
sm.print_table()
print()

is_successful = True
i = 0
j = 0
element = -1

while is_successful:
    is_successful, i, j, e = sm.pick_element()
    if not is_successful:
        break
    print(f"Разрешающий элемент `table[{i}][{j}]` = {e}")
    sm.recalculate_matrix()
    sm.print_table()
    x1, x2 = sm.find_optimum()
    print(f"Текущая точка: ({round(x1, 6)}, {round(x2, 6)}), F(x1,x2)={round(sm.f(x1, x2), 6)}")
    print()

x1, x2 = sm.find_optimum()
print(f"Решение: ({round(x1, 6)}, {round(x2, 6)}), F(x1,x2)={round(sm.f(x1, x2), 6)}")
