from core.CoreUtils import add_clause, to_dimacs_cnf

import numpy as np

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
ap.add_argument("-c", "--cutoff", required=False, type=int, help="The maximum number of clause generation resamples.",
                default=10000)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-o", "--opts", required=False, default="", help="Command line arguments to solver")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
ap.add_argument("-e", "--email", required=False, help="E-mail address for notification of instance.", default="")
ap.add_argument("-p", "--pwd", required=False, help="Password for given E-mail address", default="")
ap.add_argument("-S", "--smtp", required=False, help="E-mail service SMTP address", default="smtp.gmail.com")
ap.add_argument("-P", "--port", required=False, type=int, help="E-mail service SMTP port", default=587)
args = vars(ap.parse_args())

"""
Responsible for running generated SAT instances, by first persisting them to disk, then calling the specified solver
along with any parameters. A solve is attempted until a timeout is met or a successful solution is found. 

In the case that a successful solution is found, keep the instance on disk, else delete. Optionally, the function is
able to send an email notification periodically whenever a solution is found (useful for exploring the search space).

Parameters:
  i.    notif_counter : total time spent solving in between email notifications
 ii.             TEXT : email notification text
iii.          clauses : randomly generated clauses representing SAT instances
 iv.           n_vars : number of variables in instance
  v. file_name_suffix : optional argument providing suffix to name of file persisted to disk
"""
def run_instance(notif_counter, TEXT, clauses, n_vars, file_name_suffix=""):
    # Convert to DIMACS format and persist to disk
    print("Writing SAT instance to file...")
    cnf_file_name = to_dimacs_cnf(clauses, n_vars, args["dir"], file_name_suffix)

    time.sleep(1)  # Wait until write is completed

    solved = False

    print("Running SAT instance...")
    try:  # Attempt to solve; if timeout, a TimeoutExpired exception is thrown
        solver = [args["solver"]] + args["opts"].split() + [cnf_file_name + ".cnf"]
        subprocess.run(solver, timeout=(args["timeout"] * 60))
        solved = True
    except subprocess.TimeoutExpired:  # if timeout occured, clear any data related to SAT instance from disk
        print("SAT solver timed out...")
        os.remove(cnf_file_name + ".cnf")
        os.remove(cnf_file_name + ".csv")
        os.remove(cnf_file_name + ".out")

    if solved:
        # read stats from csv: [0] t_read, [1] n, [2] m, [3] l, [4] t_solve, [5] n_threads, [6] n_iterations
        stats = np.genfromtxt(cnf_file_name + ".csv", delimiter=",",
                                     dtype=[float, int, int, int, float, int, int])
        stats = np.atleast_1d(stats)

        tD = stats[0][4]  # extract solve time
        notif_counter = notif_counter + tD  # update counter in between solves

    if args["email"] != "":  # if email notifications requested
        if solved:  # update email body with new SAT instance statistics if solved
            TEXT = TEXT + cnf_file_name + " : n_vars = " + str(n_vars) + ", n_clauses = " + str(len(clauses)) +\
                   ", time = " + str(tD) + " seconds\n"

        if (3600 <= notif_counter) and TEXT != "":  # if SAT instances found and time has elapsed to send notification
            # compose email and send using the passed parameters

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
    # Initialisation

    TEXT = ""
    notif_counter = 0

    random.seed()
    n_vars = args["vars"]

    while 1:  # generate random SAT instances until user termination
        print("====================================================\nGenerating SAT instance...")

        variables = list(range(1, n_vars + 1))  # randomly select number of variables
        variables_counts = [0] * len(variables)  # initialise array to hold number of clauses in which each var occurs

        clauses_arr = set([])  # clauses maintained as a set; we will maintain clauses as a hashable type and in this
                               # manner we will ensure that each clause added is unique ie. sampling without replacement

        n_clauses = 0  # maintain count of number of clauses added

        # maximum number of clauses in which a variable can appear in, to satisfy the ALLL conditions
        max_var_clauses = math.floor(math.pow(2, args["literals"]) / (args["literals"] * math.e))

        bias = 1.0 / args["bias"]  # parameter controlling the 'degree' by which the ALLL conditions are broken

        while args["literals"] < len(variables):  # while enough variables are available to form a new clause with k literals
            n_clauses = n_clauses + 1  # update clause count

            # fetch new clause; may update variables and variables_counts (in particular it may delete a variable from
            # the array, meaning that max_var_clauses has been exceeded for that variable)
            clause, variables, variables_counts, failed = add_clause(variables, variables_counts, args["literals"],
                                                                     max_var_clauses, bias, clauses_arr,
                                                                     args["cutoff"])
            if not failed:
                clauses_arr.add(clause)
            else:
                break

        notif_counter, TEXT = run_instance(notif_counter, TEXT, clauses_arr, n_vars)  # run generated SAT instance
