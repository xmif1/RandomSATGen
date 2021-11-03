import os
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
ap.add_argument("-t", "--timeout", required=False, type=int, help="The timeout in minutes.", default=30)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
ap.add_argument("-e", "--email", required=False, help="E-mail address for notification of instance.", default="")
ap.add_argument("-p", "--pwd", required=False, help="Password for given E-mail address", default="")
ap.add_argument("-S", "--smtp", required=False, help="E-mail service SMTP address", default="smtp.gmail.com")
ap.add_argument("-P", "--port", required=False, type=int, help="E-mail service SMTP port", default=587)
args = vars(ap.parse_args())


def add_clause(n_vars, max_n_literals, clauses_arr, parent_clause=None):
    if parent_clause is None:
        parent_clause = []

    random.seed()

    clause = []

    sampling_size = 0
    if 0 < len(parent_clause):
        sampling_size = random.randint(1, len(parent_clause))
        if sampling_size == max_n_literals:
            sampling_size = sampling_size - 1

        sampling = random.sample(parent_clause, sampling_size)
        for s in sampling:
            clause.append(int(s * random.choice([1, -1])))

    for _ in range(random.randint(1, max_n_literals - sampling_size)):
        rand_literal = 0

        while 1:
            rand_literal = random.randint(-n_vars - 1, n_vars + 1)
            if rand_literal == 0:
                continue

            in_clauseQ = False
            for c in clause:
                if rand_literal == c or rand_literal == -c:
                    in_clauseQ = True
                    break

            if not in_clauseQ:
                break

        clause.append(rand_literal)

    clauses_arr.append(clause)

    return clauses_arr


def max_degree(clause_size):
    d = ((2**clause_size)/math.e) - 1
    if d <= 0:
        return 1
    elif math.log2(d) <= 0:
        return 1
    else:
        return 1 + math.floor(math.log2(d))


def to_dimacs_cnf(clauses_arr, n_vars):
    gen_time = datetime.datetime.now()
    s = "c RandomSATGen Instance\nc Generated on " + gen_time.strftime("%d/%m/%Y, %H:%M:%S") + "\np cnf " \
        + str(n_vars) + " " + str(len(clauses_arr))

    for c in clauses_arr:
        s = s + "\n"

        for l in c:
            s = s + str(l) + " "

        s = s + "0"

    return gen_time, s


if __name__ == "__main__":
    TEXT = ""
    notif_counter = 0

    while 1:
        clauses_arr = []
        curr_clauses_arr = []
        n_vars = random.randint(math.floor(args["vars"] / 2), args["vars"])
        n_clauses = random.randint(n_vars, args["clauses"])

        for _ in range(random.randint(1, 1 + math.ceil(n_vars / args["literals"]))):
            curr_clauses_arr = add_clause(n_vars, args["literals"], curr_clauses_arr)

        max_clauses = False
        while 1:
            temp_clauses_arr = []

            for c in curr_clauses_arr:
                d = max_degree(len(c))
                for _ in range(random.randint(0, d)):
                    if (len(clauses_arr) + len(curr_clauses_arr) + len(temp_clauses_arr)) < n_clauses:
                        temp_clauses_arr = add_clause(n_vars, args["literals"], temp_clauses_arr, parent_clause=c)
                    else:
                        max_clauses = True
                        break

                if max_clauses:
                    break

            if max_clauses:
                clauses_arr = clauses_arr + curr_clauses_arr + temp_clauses_arr
                break
            else:
                clauses_arr = clauses_arr + curr_clauses_arr
                curr_clauses_arr = temp_clauses_arr

        gen_time, s = to_dimacs_cnf(clauses_arr, n_vars)

        cnf_file_name = args["dir"] + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + ".cnf"
        cnf_file = open(cnf_file_name, "w")
        cnf_file.write(s)
        cnf_file.close()

        t0 = datetime.datetime.now()
        solved = False

        try:
            subprocess.run([args["solver"], cnf_file_name], timeout=(args["timeout"]*60))
            solved = True
        except subprocess.TimeoutExpired:
            os.remove(cnf_file_name)
            os.remove(args["dir"] + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + ".out")

        t1 = datetime.datetime.now()

        tD = (t1 - t0).total_seconds()
        notif_counter = notif_counter + tD

        if args["email"] != "":
            if solved:
                TEXT = TEXT + cnf_file_name + " : n_vars = " + str(n_vars) + ", n_clauses = " + str(n_clauses) +\
                       ", time = " + str(tD) + " seconds\n"

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

                    notif_counter = 0
                    TEXT = ""
                except Exception:
                    print("Unable to communicate with mailing service")
                    exit(1)
