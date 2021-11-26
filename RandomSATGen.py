import os
import time
import math
import random
import smtplib
import datetime
import argparse
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("-n", "--vars", required=True, type=int, help="The maximum number of variables in an instance.")
# ap.add_argument("-m", "--clauses", required=True, type=int, help="The maximum number of clauses in an instance.")
ap.add_argument("-k", "--literals", required=True, type=int, help="The number of literals in a clause.")
# ap.add_argument("-c", "--components", required=False, type=int, help="The maximum number of components.", default=10)
ap.add_argument("-t", "--timeout", required=False, type=int, help="The timeout in minutes.", default=30)
ap.add_argument("-b", "--bias", required=False, type=float, help="The bias with which to prune a clause", default=0)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
ap.add_argument("-e", "--email", required=False, help="E-mail address for notification of instance.", default="")
ap.add_argument("-p", "--pwd", required=False, help="Password for given E-mail address", default="")
ap.add_argument("-S", "--smtp", required=False, help="E-mail service SMTP address", default="smtp.gmail.com")
ap.add_argument("-P", "--port", required=False, type=int, help="E-mail service SMTP port", default=587)
args = vars(ap.parse_args())


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


def run_instance(notif_counter, TEXT, clauses, n_vars, n_components, file_name_suffix=""):
    signed_clauses = []
    for clause in clauses:
        signed_clauses.append([x * y for x, y in zip(clause[0], clause[1])])

    gen_time, s = to_dimacs_cnf(signed_clauses, n_vars)

    cnf_file_name = args["dir"] + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + file_name_suffix + ".cnf"
    cnf_file = open(cnf_file_name, "w")
    cnf_file.write(s)
    cnf_file.close()

    time.sleep(1)

    t0 = datetime.datetime.now()
    solved = False

    try:
        subprocess.run([args["solver"], cnf_file_name], timeout=(args["timeout"] * 60))
        solved = True
    except subprocess.TimeoutExpired:
        os.remove(cnf_file_name)
        os.remove(args["dir"] + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + file_name_suffix + ".out")

    t1 = datetime.datetime.now()

    tD = (t1 - t0).total_seconds()
    notif_counter = notif_counter + tD

    if args["email"] != "":
        if solved:
            TEXT = TEXT + cnf_file_name + " : n_vars = " + str(n_vars) + ", n_clauses = " \
                   + str(len(signed_clauses)) + ", n_components = " + str(n_components) + ", time = " + str(tD) + \
                   " seconds\n"

        if (3600 <= notif_counter) and TEXT != "":
            TEXT = "SAT instances found! Details:\n\n" + TEXT

            FROM = args["email"]
            TO = [args["email"]]

            email_time = datetime.datetime.now()
            SUBJECT = "RandomSATGen Update (" + email_time.strftime("%d/%m/%Y %H:%M:%S") + ")"

            message = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (FROM, ", ".join(TO), SUBJECT, TEXT)
            try:
                server = smtplib.SMTP(args["smtp"], args["port"])
                server.ehlo()
                server.starttls()
                server.login(args["email"], args["pwd"])
                server.sendmail(FROM, TO, message)
                server.close()

                return 0, ""
            except Exception:
                print("Unable to communicate with mailing service")
                exit(1)

    return notif_counter, TEXT


if __name__ == "__main__":
    TEXT = ""
    notif_counter = 0

    random.seed()

    while 1:
        full_clauses_arr = []
        n_vars = random.randint(math.floor(args["vars"] / 2), args["vars"])
        # n_components = random.randint(1, args["components"])
        components = get_components(n_vars, 1)

        for variables in components:
            if len(variables) == 0:
                variables = range(1, 2)
                variables_counts = [0]
            else:
                variables_counts = [0] * len(variables)

            clauses_arr = []
            max_var_clauses = math.floor(math.pow(2, args["literals"]) / (args["literals"] * math.e))

            n_clauses = 0
            while args["literals"] < len(variables):
                n_clauses = n_clauses + 1

                clause, variables, variables_counts = add_clause(variables, variables_counts, args["literals"],
                                                                 max_var_clauses, args["bias"])
                clauses_arr.append(clause)

            full_clauses_arr = full_clauses_arr + clauses_arr

        notif_counter, TEXT = run_instance(notif_counter, TEXT, full_clauses_arr, n_vars, 1, "__pruned")
