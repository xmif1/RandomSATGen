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
ap.add_argument("-s", "--solver", required=True, help="Path to a solver instance accepting a DIMACS CNF file as input.")
ap.add_argument("-d", "--dir", required=True, help="Path to directory where to save CNF files.")
args = vars(ap.parse_args())

if __name__ == "__main__":
    random.seed()

    for k in range(3, 9):
        b_arr = []
        t_arr = []
        m_arr = []

        for b in range(1, 101):
            mTotal = 0
            tTotal = 0
            n_attempts = 0
            n_executions = 0

            while n_executions < 10 and n_attempts < 5:
                variables = list(range(1, args["vars"] + 1))
                variables_counts = [0] * len(variables)

                clauses_arr = []
                max_var_clauses = math.floor(math.pow(2, k) / (k * math.e))

                n_clauses = 0
                while k < len(variables):
                    n_clauses = n_clauses + 1

                    clause, variables, variables_counts = add_clause(variables, variables_counts, k, max_var_clauses,
                                                                     1.0 / b)
                    clauses_arr.append(clause)

                signed_clauses = []
                for clause in clauses_arr:
                    signed_clauses.append([x * y for x, y in zip(clause[0], clause[1])])

                gen_time, s = to_dimacs_cnf(signed_clauses, args["vars"])

                cnf_file_name = args["dir"] + "rand_cnf_" + gen_time.strftime("%d_%m_%Y_%H_%M_%S") + "_analysis.cnf"
                cnf_file = open(cnf_file_name, "w")
                cnf_file.write(s)
                cnf_file.close()

                time.sleep(1)

                t0 = datetime.datetime.now()
                try:
                    subprocess.run([args["solver"], cnf_file_name], timeout=600)

                    n_executions = n_executions + 1
                    t1 = datetime.datetime.now()
                    mTotal = mTotal + n_clauses
                    tTotal = tTotal + (t1 - t0).total_seconds()
                except subprocess.TimeoutExpired:
                    n_attempts = n_attempts + 1

            if n_attempts < 5:
                b_arr.append(1/b)
                t_arr.append(tTotal / n_executions)
                m_arr.append(math.floor(mTotal / n_executions))
            else:
                break

        csv_name = args["dir"] + "csv/analysis_n" + str(args["vars"]) + "_k" + str(k) + ".csv"
        with open(csv_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([b_arr, t_arr, m_arr])

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
        fig.set_canvas(plt.gcf().canvas)

        ax1.plot(b_arr, t_arr)
        ax1.set_xlabel('$\epsilon$')
        ax1.set_ylabel('$t$')

        ax2.plot(b_arr, m_arr)
        ax2.set_xlabel('$\epsilon$')
        ax2.set_ylabel('$m$')

        ax3.plot(m_arr, t_arr)
        ax3.set_xlabel('$m$')
        ax3.set_ylabel('$t$')

        fig.set_size_inches(8, 23)
        plt.tight_layout()

        pdf_name = args["dir"] + "pdf/analysis_n" + str(args["vars"]) + "_k" + str(k) + ".pdf"
        fig.savefig(pdf_name, format='pdf', bbox_inches='tight')
