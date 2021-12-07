import random
import datetime


def add_clause(vars, var_counts, n_literals, max_var_clauses, bias):
    clauses_vars = random.sample(vars, n_literals)
    clauses_signs = random.choices([-1, 1], k=n_literals)

    for v in clauses_vars:
        var_counts[v-1] = var_counts[v-1] + 1
        if max_var_clauses < var_counts[v-1] and random.random() < bias:
            vars.remove(v)

    return [clauses_vars, clauses_signs], vars, var_counts


def to_dimacs_cnf(clauses_arr, n_vars):
    gen_time = datetime.datetime.now()
    s = "c RandomSATGen Instance\nc Generated on " + gen_time.strftime("%d/%m/%Y, %H:%M:%S") + "\np cnf " \
        + str(n_vars) + " " + str(len(clauses_arr)) + "\n"

    for c in clauses_arr:
        for l in c:
            s = s + str(l) + " "

        s = s + "0\n"

    return gen_time, s


def get_components(n_vars, n_components):
    if n_components == 1:
        return [list(range(1, n_vars + 1))]
    else:
        components = []
        split = random.sample(range(2, n_vars), n_components - 1)
        split.sort()

        components.append(list(range(1, split[0])))

        for s in range(len(split) - 1):
            components.append(list(range(split[s], split[s + 1])))

        s = len(split) - 1
        components.append(list(range(split[s], n_vars + 1)))

        return components