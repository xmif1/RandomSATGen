import random
import datetime


def add_clause(vars, var_counts, k, max_var_clauses, bias, clauses_arr, max_tries):
    unique = False
    failed = False
    count = 0

    while not unique and not failed:
        count = count + 1
        clauses_vars = random.sample(vars, k)
        clauses_signs = random.choices([-1, 1], k=k)
        clause = frozenset([x * y for x, y in zip(clauses_vars, clauses_signs)])

        unique = True
        if clause in clauses_arr:
            unique = False
            if max_tries <= count:
                failed = True

    if failed:
        return [None, None], None, None, True
    else:
        for v in clauses_vars:
            var_counts[v-1] = var_counts[v-1] + 1
            if max_var_clauses < var_counts[v-1] and random.random() < bias:
                vars.remove(v)

        return clause, vars, var_counts, False


def to_dimacs_cnf(clauses_arr, n_vars, dir, file_name_suffix):
    gen_time = datetime.datetime.now()
    cnf_file_name = dir + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + file_name_suffix + ".cnf"
    cnf_file = open(cnf_file_name, 'a')

    s = "c RandomSATGen Instance\nc Generated on " + gen_time.strftime("%d/%m/%Y, %H:%M:%S") + "\np cnf " \
        + str(n_vars) + " " + str(len(clauses_arr)) + "\n"
    cnf_file.write(s)

    for c in clauses_arr:
        s = ""

        for l in c:
            s = s + str(l) + " "

        s = s + "0\n"
        cnf_file.write(s)

    cnf_file.close()

    return cnf_file_name, gen_time
