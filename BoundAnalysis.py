import numpy as np

from core.CoreUtils import add_clause, to_dimacs_cnf
from matplotlib import pyplot as plt

import os
import csv
import math
import time
import random
import argparse
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("-n", "--vars", required=True, type=int, help="The maximum number of variables in an instance.")
ap.add_argument("-km", "--k-min", required=True, type=int, help="The minimum value of k.")
ap.add_argument("-kM", "--k-max", required=True, type=int, help="The maximum value of k.")
ap.add_argument("-kS", "--k-step", required=False, type=int, help="Step between min and max values of k.", default=1)
ap.add_argument("-i", "--iterations", required=True, type=int, help="The maximum number of sequential solve iterations.")
ap.add_argument("-c", "--cutoff", required=False, type=int, help="The maximum number of clause generation resamples.",
                default=10000)
ap.add_argument("-N", "--samples", required=False, type=int,
                help="The number of samples equally spaced between 0 and 1.", default=100)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-o", "--opts", required=False, default="", help="Command line arguments to solver")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
ap.add_argument("-t", "--timeout", required=False, type=int, help="Timeout in seconds.", default=30)
args = vars(ap.parse_args())

if __name__ == "__main__":
    random.seed()

    # Carry out benchmark for every number of literals k between k_min and k_max, using an interval of k_step
    for k in range(args["k_min"], args["k_max"] + 1, args["k_step"]):
        # Maximum number of clauses a variable can appear in without breaking the ALLL conditions
        max_var_clauses = math.floor(math.pow(2, k) / (k * math.e))

        # Initialise data collection structures...
        b_arr = []  # Store bias values b
        t_arr = []  # Store average solve times values t
        m_arr = []  # Store average number of clauses m
        i_arr = []  # Store average number of solve iterations i

        b_max = 0  # Maximum bias value before solve time timeout reached...

        # For every geometrically spaced bias value (ie. we vary the degree by which the ALLL conditions are broken and
        # record the behaviour of the solver through the various statistics recorded)
        for b in np.geomspace(1, 1/args["samples"], args["samples"]):

            # Store aggregate data to be averaged over 10 tests (in this manner we reduce noise in the data)
            mTotal = 0
            tTotal = 0
            iTotal = 0
            n_executions = 0

            # Run benchmarks for 10 times for the given number of literals k and bias b, to average and reduce noise
            while n_executions < 10:
                variables = list(range(1, args["vars"] + 1))  # randomly select number of variables
                variables_counts = [0] * len(variables)  # initialise array to hold number of clauses in which each var occurs

                clauses_arr = set([]) # clauses maintained as a set; we will maintain clauses as a hashable type and in this
                                      # manner we will ensure that each clause added is unique ie. sampling without replacement

                n_clauses = 0  # maintain count of number of clauses added
                while k < len(variables):  # while enough variables are available to form a new clause with k literals
                    n_clauses = n_clauses + 1  # update clause count

                    # fetch new clause; may update variables and variables_counts (in particular it may delete a variable from
                    # the array, meaning that max_var_clauses has been exceeded for that variable)
                    clause, variables, _, failed = add_clause(variables, variables_counts, k, max_var_clauses, b,
                                                              clauses_arr, args["cutoff"])
                    if not failed:
                        clauses_arr.add(clause)
                    else:
                        break

                # Convert to DIMACS format and persist to disk
                cnf_file_name = to_dimacs_cnf(clauses_arr, args["vars"], args["dir"], "_analysis")

                time.sleep(1)  # Wait until write is completed

                try:  # Attempt to solve; if timeout, a TimeoutExpired exception is thrown
                    solver = [args["solver"]] + args["opts"].split() + [cnf_file_name + ".cnf"]
                    subprocess.run(solver, timeout=args["timeout"])
                except subprocess.TimeoutExpired:  # if timeout occured, clear any data related to SAT instance from disk
                    os.remove(cnf_file_name + ".cnf")
                    os.remove(cnf_file_name + ".csv")
                    os.remove(cnf_file_name + ".out")

                    b_max = b  # store value of bias before timeout (no further analysis will be carried out)
                    break

                # Clean-up any files no longer required
                os.remove(cnf_file_name + ".cnf")
                os.remove(cnf_file_name + ".out")

                # read stats from csv: [0] t_read, [1] n, [2] m, [3] l, [4] t_solve, [5] n_threads, [6] n_iterations
                stats = np.genfromtxt(cnf_file_name + ".csv", delimiter=",",
                                      dtype=[float, int, int, int, float, int, int])
                stats = np.atleast_1d(stats)
                os.remove(cnf_file_name + ".csv")  # Clean-up any files no longer required

                if args["iterations"] < stats[0][6]:  # If timeout not reached but maximum number of solver iterations reached...
                    b_max = b
                    break

                # Record gathered data
                n_executions = n_executions + 1
                mTotal = mTotal + n_clauses
                tTotal = tTotal + stats[0][4]
                iTotal = iTotal + stats[0][6]

            if b_max == 0:  # If successfully gathered all data, average and record results
                b_arr.append(1 - b)
                t_arr.append(tTotal / n_executions)
                m_arr.append(math.floor(mTotal / n_executions))
                i_arr.append(iTotal / n_executions)
            else:
                break

        # Store results in a CSV file, for possible further future analysis
        csv_name = args["dir"] + "analysis_n" + str(args["vars"]) + "_k" + str(k) + ".csv"
        with open(csv_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([b_arr, t_arr, m_arr, i_arr])

        # ================================================== Plotting ==================================================

        if b_max != 0:
            E = 1 - b_max
        else:
            E = 1 - (1 / args["samples"])

        ttl = "n = " + str(args["vars"]) + ", k = " + str(k) + ", $\delta_{\mathrm{max}}$ = " + str(E)

        fig, (ax) = plt.subplots(1, 1)
        fig.set_canvas(plt.gcf().canvas)
        fig.suptitle(ttl)

        ax.plot(m_arr, i_arr, 'r', label='Empirical data')
        ax.plot(m_arr, i_arr, 'r+')

        upperBound = np.multiply((np.e / (2**k - (k*np.e))),  m_arr)
        ax.plot(m_arr, upperBound, 'b', label="$i(m) = \dfrac{em}{2^k - ke}$")

        ax.legend()
        ax.set_xlabel('$m$' + " (clauses)")
        ax.set_ylabel('$i$' + " (iterations)")

        fig.set_size_inches(9, 6)
        plt.tight_layout()

        pdf_name = args["dir"] + "analysis_n" + str(args["vars"]) + "_k" + str(k)
        fig.savefig(pdf_name + ".pdf", format='pdf', bbox_inches='tight')
