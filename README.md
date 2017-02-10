# Task Variant Allocation in Distributed Robotics

This repository contains the input files, source code, plotting scripts and instructions required to recreate the work from the paper:

"Task Variant Allocation in Distributed Robotics"

by José Cano, David R. White, Alejandro Bordallo, Ciaran McCreesh, Patrick Prosser, Jeremy Singer and Vijay Nagarajan.

The paper appeared in Robotics Science and Systems 2016, an academic conference. The website of RSS 2016 is at:

http://rss2016.engin.umich.edu/

## Further Information

For futher details of this work, please consult the paper or contact one of the following main authors:

José Cano: jcanore@inf.ed.ac.uk
David R. White: david.r.white@ucl.ac.uk

## Requirements

* Python 2.7 for our experimentation scripts
* Pyton packages: shortuuid
* The R package for plotting results from Section V-E
* The MiniZinc constraint modeller
* The Qt5 library (libQt5)

### Python Packages

To install shortuuid:

    sudo pip install shortuuid

### MiniZinc 

The only unusual requirement here is the MiniZinc constraint solver. MiniZinc can be downloaded from:

http://www.minizinc.org

We had some problems with MiniZinc during our work, particularly with regards to it crashing sometimes, and we also found that the results produced from version to version. Therefore, we recommend downloading *MiniZinc 2.0.11*. 

You can find more MiniZinc downloads at:

https://github.com/MiniZinc/MiniZincIDE/releases/

Note that you'll need the *bundled* package.

The download should be placed in the root directory of this repository, i.e. in task_alloc/

If you're using OS X, then after opening the .dmg file, you can click and drag MiniZinc into task_alloc/ instead of Applications.

If you examine src/minizinc.sh, you'll see a bit of a hack - a hardcoded check for Linux/OS X in bash, in order to select the right directory for MiniZinc. You may need to change this file in order to recreate our work on Windows. Try running it directly if you're having problems with MiniZinc experiments.

## Overview of the files in this Repository

* experiments/ - contains the input CSV files for the experiments.
* original_results/ - contains the output CSV files we used in the paper.
* plot/ - contains R scripts for plotting the diagrams from Section V-C.
* src/sim - contains the Python scripts that implement the three solution methods, and for running the experiments. 

## Description of the System

src/sim/task_experiments.py is the main entry point for experiments. It is supplied with a CSV file containing the experiments to be run: one experiment per line, so that if (for example) we need to run 10 repetitions, then we must include 10 lines in the input CSV file.
 
Its usage is straightforward:

    python task_experiments.py <input.csv>
    
task_greedy, _local, and _minizinc all implement solvers that are called by task_experiments.py accordingly.

task_model.py is a model of the problem: along with task_score.py, it implements the modelling found in Section II (Problem Formulation) in the paper.

We also had scripts and files that enabled us to specify problems in XML (the graphml format), log various files including problem descriptions and MiniZinc input files so that we could manually examine them. If you'd like to somehow extend our work and these files would be useful, please get in touch with the authors as described above.

## Reminder of the Experiments

The experimentation in the paper consisted of three parts:

* Section V-C, running each problem solver on each problem/scenario.
* Section V-E, treating MiniZinc and local search as "anytime" solvers.
* Other work running experiments on the case study robotics platform.

The final set of experiments are too complex and involved to provide a simple method of reproducing our results. If you're interested in replicating this work, then please contact José Cano as described above.

The other experiments are quite straightforward to rerun. However, keep in mind that your results will not perfectly reflect our work, even if running on the same hardware and using the seeds we provide where applicable.

## Examining our Original Results

You can examine our original results, used for plotting the figures in the paper, in the original_results/ directory. This directory contains CSV output files containing our results and are quite self-explanatory. You can regenerate our plots using the R scripts in the plot/ directory.

## Recreating our Results

A slight _mea culpa_ here: the value SERVER_FACTOR in task_problem should really have been parameterised rather than hard-coded. I (David) believe that this value was set to 4 at all times during our experimentation; it may have been 3, particularly during the experimentation described in Section V-E. In other words, we think we've got this right, but if something doesn't look the same, it is something worth tweaking.

### Running Experiments

To recreate our results, it is simply a matter of using task_experiments.py with the relevant input files found in the experiments/ directory:

* section_v_c_greedy.csv - Run the greedy algorithm on all problems
* section_v_c_local.csv - Run the local search on all problems for a timeout (approx amount of time MiniZinc takes to solve the problem)
* section_v_c_local_2.csv - Repeat the local search
* section_v_c_local_3.csv - And again
* section_v_c_minizinc.csv - Run MiniZinc on all problems
* section_v_e_anytime_problem7.csv - Run MiniZinc and local search with varying time limits for Problem 7
* section_v_e_anytime_problem7_reps.csv - Verify the variance in anytime local search performance on Problem 7
* section_v_e_anytime_problem8.csv - Run MiniZinc and local search with a time limit for Problem 8

Firstly, change to the src/sim directory.

Then run (for the first experiment):

    python task_experiments.py ../../experiments/section_v_c_greedy.csv

The results will be placed in the experiments directory, with _results.csv appended to the filename.

Please note that we do not provide the files for plotting the results in Section V-C. This omission is simply because their creation was a convoluted and somewhat manual process (it did not use R). It shouldn't be much work to recreate these plots simply in, for example, Excel or gnuplot.

### Plotting Figures

R scripts are provided in the "plot" directory to recreate Figures 4a, 4b, and 4c.

To run the scripts, change to the "plot" directory and run (for example):

    r -f plot_7.r
    
The output, problem7.pdf, will be left in the same directory.

# Further Information

For futher details of this work, please consult the paper or contact one of the following main authors:

José Cano: jcanore@inf.ed.ac.uk
David R. White: david.r.white@ucl.ac.uk