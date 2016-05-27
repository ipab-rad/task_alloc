import task_problem
import task_model as model
import task_local as local_search
import task_greedy as greedy_heuristic
import task_minizinc as cp_minizinc
import signal
import csv
import task_score
import sys
import os
import time
import random

INSTANCES = [
    { 'processors': 2, 'robots': 1, 'cameras': 1},
    { 'processors': 2, 'robots': 1, 'cameras': 2},
    { 'processors': 2, 'robots': 1, 'cameras': 3},
    { 'processors': 3, 'robots': 2, 'cameras': 1},
    { 'processors': 3, 'robots': 2, 'cameras': 2},
    { 'processors': 3, 'robots': 2, 'cameras': 3},
    { 'processors': 4, 'robots': 3, 'cameras': 1},
    { 'processors': 4, 'robots': 3, 'cameras': 2},
    { 'processors': 4, 'robots': 3, 'cameras': 3},
    { 'processors': 4, 'robots': 3, 'cameras': 4}
]

INPUT_HEADER = ['method', 'problem', 'timeout', 'seed']
OUTPUT_HEADER = INPUT_HEADER + ['known_optimal', 'all_assigned', 'feasible', 'time', 'utilisation', 'bandwidth', 'residency', 'coresidency', 'qos', 'freecycles', 'solution']
# Global flag, yuck
written_header = False

def process_exp_file(exp_filename):
    problems = gen_all_problems()
    dump_problems(problems)
    output_filename = gen_output_filename(exp_filename)
    write_header(output_filename)
    with open(exp_filename, 'rU') as exp_file:
        exp_reader = csv.DictReader(exp_file)
        for row in exp_reader:
          print 'Running exp: ' + row['method'] + ' on problem: ' + row['problem'] + ' timeout: ' + row['timeout']
          if row['method'] == 'local':
              if row['seed']:
                  random.seed(int(row['seed']))
              else:
                  print "Provide a seed when running local search."
                  sys.exit(-1)
          problem_no = int(row['problem'])
          if problem_no < 1:
              print "Error in input file: Problem numbers begin at 1."
              sys.exit(-1)
          problem = problems[problem_no-1]
          timeout = int(row['timeout'])
          elapsed, known_optimal, solution = eval(row['method'])(problem, timeout)
          result = score(problem, solution)
          result['time'] = elapsed
          result['known_optimal'] = known_optimal
          result['solution'] = str(solution)
          result['all_assigned'] = task_score.all_tasks_assigned(problem, solution)
          result.update(row)
          write_result(output_filename, result)
          write_solution_description(row['method'],row['problem'], solution)
          print str(solution)

def write_solution_description(method, problem, solution):
    filename = 'output/' + method + '_' + problem + '.txt'
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        os.makedirs(d)
    with open(filename,'w') as output_file:
        if solution:
            desc = solution.long_desc()
        else:
            desc = 'No solution generated.'
        output_file.write(desc)

def gen_output_filename(exp_filename):
    output_name = os.path.splitext(exp_filename)[0]
    output_name += '_results.csv'
    return output_name

def gen_all_problems():
    problems = []
    for instance in INSTANCES:
        num_processors = instance['processors']
        num_robots = instance['robots']
        num_cameras = instance['cameras']
        p = task_problem.generate(num_processors, num_robots, num_cameras)
        problems.append(p)
    return problems


def dump_problems(problems):
    with open('detailed_problems', 'w') as detail:
        n = 0
        for p in problems:
            n += 1
            detail.write("*** PROBLEM " + str(n) + ' ***\n')
            detail.write(str(p))
            detail.write('\n')
            detail.flush()


def score(problem, assignment):
    if assignment:
        subscores = task_score.subscores(problem, assignment)
        feasible = task_score.feasible_score(subscores)
    else:
        subscores = (0, 0, 0, 0, 0, 0)
        feasible = False
    s =  {'utilisation': subscores[0], 'bandwidth': subscores[1], 'residency': subscores[2],
            'coresidency': subscores[3], 'qos': subscores[4], 'freecycles': subscores[5]}
    s['feasible'] = feasible
    return s


def write_header(output_filename):
    with open(output_filename, 'w') as output_file:
        exp_writer = csv.DictWriter(output_file, OUTPUT_HEADER)
        exp_writer.writeheader()
        output_file.flush()


def write_result(output_filename, res):
    with open(output_filename, 'a') as output_file:
        exp_writer = csv.DictWriter(output_file, OUTPUT_HEADER)
        exp_writer.writerow(res)
        output_file.flush()


# Each method must return a tuple (time, known_optimal, solution)

def local(problem, timeout):
    search = local_search.LocalSearch(problem)
    start = time.time()
    call_timeout(search.solve, timeout)
    elapsed = time.time() - start
    assignment = search.best_assignment
    return elapsed, False, assignment


def choco(problem, timeout):
    return call_timeout(cp_choco.solve, timeout, problem)


def greedy(problem, timeout):
    start = time.time()
    res = call_timeout(greedy_heuristic.solve, timeout, problem)
    elapsed = time.time() - start
    return elapsed, False, res


def minizinc(problem, timeout):
    elapsed, solution, optimal = cp_minizinc.solve(timeout, problem)
    if solution:
        assignment = model.Assignment()
        for v_id in range(1, len(solution)+1):
            if solution[v_id-1] != 0:
                variant = problem.variant(v_id)
                processor = solution[v_id-1]
                assignment.assign(variant, problem.processor(processor))
    else:
        assignment = None
    return elapsed, optimal, assignment



class TimeoutException(Exception):
    pass


def call_timeout(fname, timeout, *arg):
    result = None
    def signal_handler(signum, frame):
        print "TIMEOUT!"
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(timeout)
    try:
        result = fname(*arg)
    except TimeoutException as e:
        print "Timeout!"
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Please provide input CSV"
        sys.exit(-1)
    print 'Reading file: ' + sys.argv[1]
    process_exp_file(sys.argv[1])
