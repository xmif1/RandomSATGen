# Random SAT Generation and ALLL Solver Analysis Tools

---

Xandru Mifsud (2022)

Undergraduate CS APT 'Random Boolean Satisfiability' (University of Malta)

Supervisor: Dr. Sandro Spina

---

## Description

The following repository consists of number of tools for generating random SAT instances that break the ALLL conditions
outlined in [1], as well as a number of performance analysis tools for both serial and parallel implementations. 

These tools are targeted at benchmarking the implementation given [here](https://github.com/xmif1/ALLLSatisfiabilitySolver/tree/dissertation).

__The code here forms the _secondary_ code artefact forming part of the CS APT, as required for the awarding of the B.Sc.
(Hons) in Computer Science and Mathematics.__

---

## Requirements

The implementation requires ```python``` version 3.7+, along with the additional packages ```numpy``` and ```matplotlib```.

## Execution Instructions

After cloning the repository, simply ```cd``` into the directory containing the Python files and execute whichever you require.

Use the ```-h``` flag to get a list of available options along with a description, for each Python file respectively.

Suggested parameters as well as sample analysis results as found within the dissertation, available upon request from the author.

---

## References

[1] R. A. Moser and G. Tardos, 'A constructive proof of the general Lovász Local Lemma' (2009), availble at: https://arxiv.org/pdf/0903.0544.pdf