import numpy as np

from core.CoreUtils import add_clause, to_dimacs_cnf
from matplotlib import pyplot as plt

import csv
import math
import time
import random
import datetime
import argparse
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("-n", "--vars", required=True, type=int, help="The maximum number of variables in an instance.")
ap.add_argument("-k1", "--k-min", required=True, type=int, help="The minimum value of k.")
ap.add_argument("-k2", "--k-max", required=True, type=int, help="The maximum value of k.")
ap.add_argument("-r", "--resamples", required=False, type=int, help="The maximum number of resamples.", default=10000)
ap.add_argument("-N", "--samples", required=False, type=int,
                help="The number of samples equally spaced samples between 0 and 1.", default=100)
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-o", "--opts", required=False, default="", help="Command line arguments to solver")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
args = vars(ap.parse_args())

if __name__ == "__main__":
    random.seed()

    for k in range(args["k_min"], args["k_max"] + 1):
        max_var_clauses = math.floor(math.pow(2, k) / (k * math.e))

        b_arr = []
        t_arr = []
        m_arr = []

        b_max = 0
        for b in np.geomspace(1, 1/args["samples"], args["samples"]):
            mTotal = 0
            tTotal = 0
            n_executions = 0

            while n_executions < 10:
                variables = list(range(1, args["vars"] + 1))
                variables_counts = [0] * len(variables)

                clauses_arr = set([])

                n_clauses = 0
                while k < len(variables):
                    n_clauses = n_clauses + 1

                    clause, variables, variables_counts, failed = add_clause(variables, variables_counts, k,
                                                                             max_var_clauses, b, clauses_arr,
                                                                             args["resamples"])
                    if not failed:
                        clauses_arr.add(clause)
                    else:
                        break

                cnf_file_name, gen_time = to_dimacs_cnf(clauses_arr, args["vars"], args["dir"], "_analysis")

                time.sleep(1)

                t0 = datetime.datetime.now()
                try:
                    solver = [args["solver"]] + args["opts"].split() + [cnf_file_name]
                    subprocess.run(solver, timeout=300)
                except subprocess.TimeoutExpired:
                    b_max = b
                    break

                t1 = datetime.datetime.now()

                n_executions = n_executions + 1
                mTotal = mTotal + n_clauses
                tTotal = tTotal + (t1 - t0).total_seconds()

            if b_max == 0:
                b_arr.append(1 - b)
                t_arr.append(tTotal / n_executions)
                m_arr.append(math.floor(mTotal / n_executions))
            else:
                break

        csv_name = args["dir"] + "csv/analysis_n" + str(args["vars"]) + "_k" + str(k) + ".csv"
        with open(csv_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([b_arr, t_arr, m_arr])

        if b_max != 0:
            E = 1 - b_max
        else:
            E = 1 - (1 / args["samples"])

        ttl = "n = " + str(args["vars"]) + ", k_min = " + str(k) + ", k_max = " + str(args["k_max"]) + \
              ", $\epsilon_{\mathrm{max}}$ = " + str(E)

        fig1, (ax1) = plt.subplots(1, 1)
        fig1.set_canvas(plt.gcf().canvas)
        fig1.suptitle(ttl)

        ax1.scatter(b_arr, t_arr)
        ax1.set_xlabel('$\epsilon$')
        ax1.set_ylabel('$t$')

        fig2, (ax2) = plt.subplots(1, 1)
        fig2.set_canvas(plt.gcf().canvas)
        fig2.suptitle(ttl)

        ax2.scatter(b_arr, m_arr)
        ax2.set_xlabel('$\epsilon$')
        ax2.set_ylabel('$m$')

        fig3, (ax3) = plt.subplots(1, 1)
        fig3.set_canvas(plt.gcf().canvas)
        fig3.suptitle(ttl)

        ax3.scatter(m_arr, t_arr)
        ax3.set_xlabel('$m$')
        ax3.set_ylabel('$t$')

        fig1.set_size_inches(9, 6)
        fig2.set_size_inches(9, 6)
        fig3.set_size_inches(9, 6)
        plt.tight_layout()

        pdf_name = args["dir"] + "pdf/analysis_n" + str(args["vars"]) + "_k" + str(k)
        fig1.savefig(pdf_name + "_1.pdf", format='pdf', bbox_inches='tight')
        fig2.savefig(pdf_name + "_2.pdf", format='pdf', bbox_inches='tight')
        fig3.savefig(pdf_name + "_3.pdf", format='pdf', bbox_inches='tight')
