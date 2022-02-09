from core.CoreUtils import add_clause, to_dimacs_cnf

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
ap.add_argument("-k", "--literals", required=True, type=int, help="The number of literals in a clause.")
ap.add_argument("-t", "--timeout", required=False, type=int, help="The timeout in minutes.", default=30)
ap.add_argument("-b", "--bias", required=False, type=float, help="The bias with which to prune a clause", default=0)
ap.add_argument("-r", "--resamples", required=False, type=int, help="The maximum number of resamples.", default=10000)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-o", "--opts", required=False, default="", help="Command line arguments to solver")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
ap.add_argument("-e", "--email", required=False, help="E-mail address for notification of instance.", default="")
ap.add_argument("-p", "--pwd", required=False, help="Password for given E-mail address", default="")
ap.add_argument("-S", "--smtp", required=False, help="E-mail service SMTP address", default="smtp.gmail.com")
ap.add_argument("-P", "--port", required=False, type=int, help="E-mail service SMTP port", default=587)
args = vars(ap.parse_args())


def run_instance(notif_counter, TEXT, clauses, n_vars, file_name_suffix=""):
    print("Writing SAT instance to file...")
    cnf_file_name, gen_time = to_dimacs_cnf(clauses, n_vars, args["dir"], file_name_suffix)

    time.sleep(1)

    t0 = datetime.datetime.now()
    solved = False

    print("Running SAT instance...")
    try:
        solver = [args["solver"]] + args["opts"].split() + [cnf_file_name]
        subprocess.run(solver, timeout=(args["timeout"] * 60))
        solved = True
    except subprocess.TimeoutExpired:
        print("SAT solver timed out...")
        os.remove(cnf_file_name)
        os.remove(args["dir"] + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + file_name_suffix + ".out")

    t1 = datetime.datetime.now()

    tD = (t1 - t0).total_seconds()
    notif_counter = notif_counter + tD

    if args["email"] != "":
        if solved:
            TEXT = TEXT + cnf_file_name + " : n_vars = " + str(n_vars) + ", n_clauses = " + str(len(clauses)) +\
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

                return 0, ""
            except Exception:
                print("Unable to communicate with mailing service")
                exit(1)

    return notif_counter, TEXT


if __name__ == "__main__":
    TEXT = ""
    notif_counter = 0

    random.seed()
    n_vars = args["vars"]

    while 1:
        print("====================================================\nGenerating SAT instance...")

        variables = list(range(1, n_vars + 1))
        variables_counts = [0] * len(variables)

        clauses_arr = set([])

        n_clauses = 0
        max_var_clauses = math.floor(math.pow(2, args["literals"]) / (args["literals"] * math.e))
        bias = 1.0 / args["bias"]

        while args["literals"] < len(variables):
            n_clauses = n_clauses + 1

            clause, variables, variables_counts, failed = add_clause(variables, variables_counts, args["literals"],
                                                                     max_var_clauses, bias, clauses_arr,
                                                                     args["resamples"])
            if not failed:
                clauses_arr.add(clause)
            else:
                break

        notif_counter, TEXT = run_instance(notif_counter, TEXT, clauses_arr, n_vars)
