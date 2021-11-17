import os
import time
import math
import random
import smtplib
import datetime
import argparse
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--vars", required=True, type=int, help="The maximum number of variables in an instance.")
ap.add_argument("-c", "--clauses", required=True, type=int, help="The maximum number of clauses in an instance.")
ap.add_argument("-l", "--literals", required=True, type=int, help="The maximum number of literals in a clause.")
ap.add_argument("-k", "--components", required=False, type=int, help="The maximum number of components.", default=10)
ap.add_argument("-t", "--timeout", required=False, type=int, help="The timeout in minutes.", default=30)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
ap.add_argument("-e", "--email", required=False, help="E-mail address for notification of instance.", default="")
ap.add_argument("-p", "--pwd", required=False, help="Password for given E-mail address", default="")
ap.add_argument("-S", "--smtp", required=False, help="E-mail service SMTP address", default="smtp.gmail.com")
ap.add_argument("-P", "--port", required=False, type=int, help="E-mail service SMTP port", default=587)
args = vars(ap.parse_args())


def prune(clauses):
    pruned_clauses = []

    def dependent(c1, c2):
        dep_literals = []
        for l in c1:
            if (l in c2) or (-l in c2):
                dep_literals.append(l)

        return dep_literals

    degrees = [0] * len(clauses)
    for i in range(len(clauses)):
        pruned_clause = (clauses[i]).copy()
        dep_clauses = []
        for j in range(i+1, len(clauses)):
            dep_literals = dependent(clauses[i], clauses[j])
            if 0 < len(dep_literals):
                dep_clauses.append((j, dep_literals))
                degrees[i] = degrees[i] + 1
                degrees[j] = degrees[j] + 1

        clause_pruned = False
        for j, literals in dep_clauses:
            if math.floor(2**(len(pruned_clause)) - 1) < degrees[i]:
                if len(literals) < len(clauses[i]):
                    pruned_clause = list(set(pruned_clause) - set(literals))
            else:
                clause_pruned = True

            degrees[j] = degrees[j] - 1

        if clause_pruned:
            pruned_clauses.append(pruned_clause)

    return pruned_clauses


def add_clause(vars, max_n_literals):
    n_literals = max_n_literals
    if (len(vars) / 2) < max_n_literals:
        n_literals = int(len(vars) / 2)
    else:
        n_literals = random.randint(1, n_literals)

    return [x * y for x, y in zip(random.sample(vars, n_literals), random.choices([-1, 1], k=n_literals))]


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
        return [range(1, n_vars + 1)]
    else:
        components = []
        split = random.sample(range(2, n_vars), n_components - 1)
        split.sort()

        components.append(range(1, split[0]))

        for s in range(len(split) - 1):
            components.append(range(split[s], split[s + 1]))

        s = len(split) - 1
        components.append(range(split[s], n_vars + 1))

        return components


def run_instance(notif_counter, TEXT, clauses, n_vars, n_components, file_name_suffix=""):
    gen_time, s = to_dimacs_cnf(clauses, n_vars)

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
                   + str(len(clauses)) + ", n_components = " + str(n_components) + ", time = " + str(tD) + \
                   " seconds\n"

        if (14400 <= notif_counter) and TEXT != "":
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
        n_components = random.randint(1, args["components"])
        components = get_components(n_vars, n_components)

        for variables in components:
            if len(variables) == 0:
                variables = range(1, 2)

            clauses_arr = []
            max_n_clauses = min(2 ** (len(variables) - 1), math.floor(args["clauses"] / n_components))
            min_n_clauses = min(2 ** (len(variables) - 1), math.ceil(n_vars / n_components))
            n_clauses = random.randint(min_n_clauses, max_n_clauses)

            for _ in range(n_clauses):
                clauses_arr.append(add_clause(variables, args["literals"]))

            full_clauses_arr = full_clauses_arr + clauses_arr

        notif_counter, TEXT = run_instance(notif_counter, TEXT, full_clauses_arr, n_vars, n_components)

        pruned_clauses = prune(full_clauses_arr)
        notif_counter, TEXT = run_instance(notif_counter, TEXT, pruned_clauses, n_vars, n_components, "__pruned")
