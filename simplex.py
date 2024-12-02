import copy
import numpy as np


class Error:
    def __init__(self, error_string):
        self.error_string = error_string
    
    def __str__(self):
        return self.error_string


class Info:
    def __init__(self, row, column, table, i, j, x1, x2, optimum):
        self.row = row.copy()
        self.column = column.copy()
        self.table = copy.deepcopy(table)
        self.i = i
        self.j = j
        self.x1 = x1
        self.x2 = x2
        self.optimum = optimum

class SimplexMethod:
    def __init__(self, constraints, function):
        self.n = len(constraints)
        self.m = len(constraints[0]) - 1
        self.invalid_index = 1 + max(self.n, self.m)
        self.function = function
        self.row = ['x' + str(_) for _ in range(1, self.m + 1)]
        self.column = ['y' + str(_) for _ in range(1, self.n + 1)]
        self.row.append('-b')
        self.column.append('f')

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
            return self.invalid_index

        x1_i = index_of('x1')
        x2_i = index_of('x2')
        x1 = 0
        x2 = 0

        if x1_i != self.invalid_index:
            x1 = self.table[x1_i][-1]
        if x2_i != self.invalid_index:
            x2 = self.table[x2_i][-1]

        return x1, x2

    def pick_element(self) -> (bool, int, int, float):
        # find negative in `-b` column
        target_row = self.invalid_index
        for idx in range(self.n):
            if self.table[idx][-1] < 0:
                target_row = idx
                break

        # if negative element in `-b` exists then seach for non negative element in row
        if target_row != self.invalid_index:
            # find non-negative element in row
            target_column = self.invalid_index
            for column in range(self.m):
                if self.table[target_row][column] > 0:
                    target_column = column
                    break

            # logic error?
            if target_column == self.invalid_index:
                raise ValueError("incorrect system")

            return True, target_row, target_column, self.table[target_row][target_column]

        # if no negative element in `-b` column then search negative in element row `c`
        target_column = self.invalid_index
        for idx in range(self.m):
            if self.table[-1][idx] < 0:
                target_column = idx
                break

        # if no negative element in `c` column, then optimum already found
        if target_column == self.invalid_index:
            x1, x2 = self.find_optimum()
            return False, x1, x2, self.f(x1, x2)

        # otherwise find max negative num:
        # `m` where (-b_m) / (table[m][neg_index]) -> max < 0
        target_row = self.invalid_index
        first_try = True
        min_val = 1

        for row in range(self.n):
            if self.table[row][target_column] == 0:
                continue

            val = self.table[row][-1] / self.table[row][target_column]

            if first_try:
                min_val = val
                target_row = row
                first_try = False
                continue

            if val == 0 and min_val > 0:
                min_val = val
                target_row = row
                continue

            if val < 0 <= min_val:
                min_val = val
                target_row = row
                continue

            if min_val <= val < 0:
                min_val = val
                target_row = row
                continue

        if first_try or min_val > 0:
            raise ValueError("simplex method does not converge")

        return True, target_row, target_column, self.table[target_row][target_column]

    def recalculate_matrix(self):
        _is_successful, r, c, _ = sm.pick_element()

        if not _is_successful:
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
        new_table[r][c] = 1.0 / self.table[r][c]

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

    def get_solution(self):
        result = []
        result.append(Info(self.row, self.column, self.table, None, None, 0, 0, 0))

        is_successful = True
        while is_successful:
            try:
                is_successful, i, j, e = self.pick_element()
            except ValueError as e:
                result.append(Error(str(e)))
                return result

            if not is_successful:
                break
            
            result[-1].i = i
            result[-1].j = j
            self.recalculate_matrix()
            x1, x2 = self.find_optimum()
            result.append(Info(self.row, self.column, self.table, None, None, x1, x2, self.f(x1, x2)))

        return result

# Constraints such as
# y = a * x1 + b * x2 + c > 0
# c = grad F(x1,x2)
# y1 = [-39.70, -96.00, 4060.80]
# y2 = [-45.50, 45.30, 600.60]
# y3 = [45.50, -7.40, -54.60]
# y4 = [24.20, 45.10, -1091.42]
# c = [-1, -1]
# y1 = [12.50, -26.60, 726.78]
# y2 = [-26.40, -18.40, 1814.48]
# y3 = [-6, 41.80, -81.00]
# y4 = [22.30, 16.20, -780.76]
# y5 = [17.50, -3.60, -105.43]
# c = [2.4, -1.15]
# y1 = [-39.00, 93.10, 113.10]
# y2 = [-45.50, 89.90, 250.25]
# y3 = [-45.50, 67.00, 441.35]
# y4 = [-45.50, 47.20, 746.20]
# y5 = [-45.50, 24.90, 1392.30]
# y6 = [-45.50, 12.90, 1810.90]
# y7 = [-45.50, 45.50, -45.50]
# c = [-1, -2.45]
# y1 = [-1.00, -1.00, -1]
# c = [-1, 0]
# y1 = [-45.50, 12.20, 1810.90]
# y2 = [-44.20, 56.30, -73.19]
# y3 = [2.50, -92.60, 3764.32]
# c = [-1, -2.45]
if __name__ == "__main__":
    # y1 = [-9.30, 0.30, 47.37]
    # y2 = [2.30, 11.70, -55.85]
    # y3 = [-5.80, -8.00, 113.48]
    # y4 = [-1.10, 9.20, -17.13]
    # c = [-3.40, -1.05]
    # y1 = [1, 0, -2]
    # c = [-1, 0]
    y1 = [1, 1, -2]
    y2 = [-1, 1, 2]
    y3 = [0, -1, 2]
    c = [-1, 0]

    sm = SimplexMethod([y1, y2, y3], c)
    result = sm.get_solution()
    for i in result:
        if type(i) == Error:
            print(i)
            break
        print("\n\n")
        print("\t".join(i.row))
        n = len(i.table)
        for row in range(n):
            print(i.column[row], end='\t')
            print("\t".join([str(round(val, 9)) for val in i.table[row]]))
        print(i.i, i.j, i.x1, i.x2, i.optimum)
# sm.print_table()
# print()

# is_successful = True
# i = 0
# j = 0
# element = -1

# while is_successful:
#     is_successful, i, j, e = sm.pick_element()
#     if not is_successful:
#     print(f"Разрешающий элемент `table[{i}][{j}]` = {e}")
#     sm.recalculate_matrix()
#     sm.print_table()
#     x1, x2 = sm.find_optimum()
#     print(f"Текущая точка: ({round(x1, 6)}, {round(x2, 6)}), F(x1,x2)={round(sm.f(x1, x2), 6)}")
#     print()

# x1, x2 = sm.find_optimum()
# print(f"Решение: ({round(x1, 6)}, {round(x2, 6)}), F(x1,x2)={round(sm.f(x1, x2), 6)}")
