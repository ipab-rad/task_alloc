import re
import subprocess
from threading import Thread
import ast
import time
import sys
import os
import signal

TEMPLATE = 'task_template.dzn'
TMP_DIR = './minizinc_tmp/'


def solve(time_limit, problem):
    prefix = filename_prefix()
    start = time.time()

    # First pass
    optimal, qos_solution, qos = solve_qos(prefix, time_limit, problem)
    elapsed = time.time() - start
    if not optimal:
        if not qos_solution:
            print "Timeout with no QOS solution"
        else:
            print "Timeout with QOS objective: " + str(qos)
        return elapsed, qos_solution, False
    remaining_time = time_limit - elapsed
    if remaining_time <= 0:
        print "No more time to run second pass"
        return elapsed, qos_solution, False

    # Second pass
    print "QOS global optimum from first pass was " + str(qos)
    optimal_util, util_solution, util = solve_util(prefix, remaining_time, problem, qos)
    elapsed = time.time() - start
    if util_solution:
        print 'Util from second pass was ' + str(util)
        return elapsed, util_solution, optimal_util
    else:
        print 'No solution for util at all'
        return elapsed, qos_solution, False



def solve_qos(prefix, timeout, problem):
    data_filename = prefix + '_qos.dzn'
    write_data(TEMPLATE, data_filename, problem)
    return run_minizinc(timeout, data_filename, prefix, problem, '../../minizinc_model/qos_tasks.mzn')


def solve_util(prefix, timeout, problem, qos):
    data_filename = prefix + '_util.dzn'
    write_data(TEMPLATE, data_filename, problem)
    with open(data_filename, 'a') as data_file:
        data_file.write('qosGoal = ' + str(qos) + ';')
    return run_minizinc(timeout, data_filename, prefix, problem, '../../minizinc_model/util_tasks.mzn')


def write_data(template_file, data_file, problem):
    with open(template_file) as f:
        template = f.read()
    model = populate(template, problem)
    with open(data_file, 'w') as dzn_file:
        dzn_file.write(model)


def run_minizinc(time_limit, data_file, prefix, problem, task_model):
    run(time_limit, data_file, prefix, task_model)
    optimal, solution, objective = parse_solution(problem, prefix)
    return optimal, solution, objective

class SubprocessTimeoutError(RuntimeError):
    """Error class for subprocess timeout."""
    pass


# Based on http://www.ostricher.com/2015/01/python-subprocess-with-timeout/
def run_command_with_timeout(cmd, timeout_sec, stdout, stderr):
    """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.
    Return subprocess exit code on natural completion of the subprocess.
    Raise an exception if timeout expires before subprocess completes."""
    # Spawn proc in a new process group so we can kill child processes
    proc = subprocess.Popen(cmd, stderr=stderr, stdout=stdout, preexec_fn=os.setsid)
    proc_thread = Thread(target=proc.communicate)
    proc_thread.start()
    proc_thread.join(timeout_sec)
    if proc_thread.is_alive():
        # Process still running - kill it and raise timeout error
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM) # kill process group
            #proc.terminate()
            #proc.kill()
        except OSError:
            # The process finished between the `is_alive()` and `kill()`
            return proc.returncode
        # OK, the process was definitely killed
        raise SubprocessTimeoutError('Process #%d killed after %f seconds' % (proc.pid, timeout_sec))
    # Process completed naturally - return exit code
    return proc.returncode


def run(time_limit, data_file, prefix, model_file):
    cmd = ['./minizinc.sh', '-a', '-s', data_file, model_file]
    print ' '.join(cmd)
    timeout = False
    ret = -999

    stdout_filename = prefix + '.stdout'
    stderr_filename = prefix + '.stderr'
    with open(stdout_filename, 'w') as stdout_file:
        with open(stderr_filename, 'w') as stderr_file:
            try:
                ret = run_command_with_timeout(cmd, timeout_sec=time_limit, stderr=stderr_file, stdout=stdout_file)
            except SubprocessTimeoutError:
                timeout = True
    return timeout, ret


def parse_solution(problem, prefix):
    stdout_filename = prefix + '.stdout'
    with open(stdout_filename) as result:
        stdout_txt = result.readlines()

    from  __builtin__ import any as b_any
    a_solution = b_any('----------' in x for x in stdout_txt)
    the_solution = b_any('==========' in x for x in stdout_txt)

    if not (a_solution or the_solution):
        return False, None, None

    stdout_txt.reverse()
    found = False
    for index, line in enumerate(stdout_txt):
        if 'assignments' in line:
            assignments = re.findall('\[.*\]', line)
            solution = ast.literal_eval(assignments[0])
            objectives = re.findall('\d+', stdout_txt[index+1])
            objective = int(objectives[0])
            found = True
            break
    if not found:
        print "ERROR - Minizinc could not parse output."
        sys.exit(-1)
    return the_solution, solution, objective


def filename_prefix():
    ensure(TMP_DIR)
    import shortuuid
    prefix =  TMP_DIR + '/' + shortuuid.uuid()
    print "Prefix for filenames is: " + prefix
    return prefix


def ensure(dir_name):
    import os
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def populate(template, problem):
    # sort the tasks by name
    tasks = problem.sorted_tasks()
    ntasks = len(tasks)

    # variant info
    variant_counts = [len(t.variants) for t in tasks]
    variants = []
    for t in tasks:
        variants += t.variants
    nvariants = sum(variant_counts)

    # processors
    sorted_p_keys = sorted(problem.processors)
    processors = [problem.processors[k] for k in sorted_p_keys]
    nprocessors = len(processors)

    model = re.sub('_NUM_TASKS', str(ntasks), template)
    model = re.sub('_NUM_VARIANTS', str(nvariants), model)
    model = re.sub('_NUM_PROCESSORS', str(nprocessors), model)

    # tasks to variants
    first_index = 1
    tasks_to_variants = '[ '
    first = True
    for num_variants in variant_counts:
        if first:
            first = False
        else:
            tasks_to_variants += ', '
        last_index = first_index + (num_variants-1)
        tasks_to_variants += str(first_index) + '..' + str(last_index)
        first_index = last_index + 1
    tasks_to_variants += ' ]'
    model = re.sub('_TASK_VARIANT_MAPPING', tasks_to_variants, model)

    # utilisations... factor out common patterns later. TODO.
    # flatten list
    variant_utils = [str(v.size) for v in variants]
    utils = '[ ' + ', '.join(variant_utils) + ']'
    model = re.sub('_UTILISATIONS', utils, model)

    # benefit
    variant_qos = [str(v.qos) for v in variants]
    qoses = '[ ' + ', '.join(variant_qos) + ']'
    model = re.sub('_QOS', qoses, model)

    # capacities
    cap = [str(p.capacity) for p in processors]
    capacities = '[ ' + ', '.join(cap) + ']'
    model = re.sub('_CAPACITIES', capacities, model)

    # bandwidths
    bandwidths = '[| '
    for task in tasks:
        first = True
        for target in tasks:
            if first:
                first = False
            else:
                bandwidths += ', '
            if task == target:
                bandwidths += '0'
            else:
                bandwidths += str(problem.sum_messages(task, target))
        bandwidths += '\n              |'
    bandwidths += ']'
    model = re.sub('_BANDWIDTHS', bandwidths, model)

    # links
    links = '[| '
    for p in processors:
        first = True
        for p2 in processors:
            if first:
                first = False
            else:
                links += ', '
            if p == p2:
                links += '-1'
            else:
                bandwidth = p.bandwidth_to(p2)
                links += str(bandwidth)
        links += '\n          |'
    links += ']'
    model = re.sub('_LINKS', links, model)

    # residency
    permitted = '['
    first_variant = True
    for variant in variants:
        if first_variant:
            first_variant = False
        else:
            permitted += ','
        if variant.residency == []:
            permitted += '0..nProcessors'
        else:
            permitted += '{0'
            for processor in variant.residency:
                permitted += ','
                permitted += str(processor.id)[1:]
            permitted += '}'
    permitted += ']'
    model = re.sub('_PERMITTED_PROCESSORS', permitted, model)

    # coresidency
    coresidency = '['
    first = True
    for task in tasks:
        if task.coresidence != []:
            if first:
                first = False
            else:
                coresidency += ','
            coresidency += '{' + task.id[1:] + ','
            first_other = True
            for other_task in task.coresidence:
                if first_other:
                    first_other = False
                else:
                    coresidency += ','
                coresidency += str(other_task.id)[1:]
            coresidency += '}'
    coresidency += ']'
    model = re.sub('_SAME_PROCESSOR', coresidency, model)

    return model

