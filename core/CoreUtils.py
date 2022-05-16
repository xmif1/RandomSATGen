import random
import datetime

"""
Responsible for the generation of a random clause and updating any state variables related to the ALLL constraints

Parameters:
  i.            vars : list of available variables that can form part of a clause
 ii.      var_counts : list of the number of clauses in which each variable appears
iii.               k : the required number of literals in the clause
 iv. max_var_clauses : the maximum number of clauses in which a variable can appear to satisfy the ALLL conditions
  v.            bias : parameter controlling the 'degree' by which the ALLL conditions are not satisfied
 vi.     clauses_arr : array of currently generated random clauses (to check if new clause is unique)
vii.        max_trys : maximum number of trys to generate a unique clause (if collisions occur with clauses in clauses_arr)
"""
def add_clause(vars, var_counts, k, max_var_clauses, bias, clauses_arr, max_trys):
    unique = False  # flag to signal unique clause
    failed = False  # flag to signal if maximum number of trys to generate a unique clause has been reached
    count = 0  # count of number of trys to generate a unique clause

    while not unique and not failed:  # until a valid clauses is generated and max_trys not reached...
        count = count + 1
        clauses_vars = random.sample(vars, k)  # randomly select k variables
        clauses_signs = random.choices([-1, 1], k=k)  # generate signs for each variable (ie. either var or its negation)
        clause = frozenset([x * y for x, y in zip(clauses_vars, clauses_signs)])  # apply signs to the selected vars

        unique = True
        if clause in clauses_arr:  # carried in O(1) time since clause is a hashable type and clauses_arr is a set acting
                                   # as a hash table
            unique = False
            if max_trys <= count:
                failed = True

    if failed:  # empty return in case max_trys reached
        return [None, None], None, None, True
    else:  # otherwise update state variables and return...
        for v in clauses_vars:  # for each variable added to the clause
            var_counts[v-1] = var_counts[v-1] + 1  # update the count of the number of clauses in which it appears

            # if ALLL conditions are broken above max_var_clauses and a random nuber is generated below the bias...
            if max_var_clauses < var_counts[v-1] and random.random() < bias:
                vars.remove(v)  # remove variables from the vars array (ie. var can no longer form part of future
                                # generated random clauses)

        return clause, vars, var_counts, False


"""
Simple utility function responsible for representing a list of clauses as a DIMACS CNF file.

Parameters:
  i.      clauses_arr : array of generated random clauses
 ii.           n_vars : number of variables in instance
iii.              dir : directory at which to persist file
 iv. file_name_suffix : argument providing suffix to name of file persisted to disk
"""
def to_dimacs_cnf(clauses_arr, n_vars, dir, file_name_suffix):
    gen_time = datetime.datetime.now()
    cnf_file_name = dir + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + file_name_suffix
    cnf_file = open(cnf_file_name + ".cnf", 'a')

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

    return cnf_file_name
