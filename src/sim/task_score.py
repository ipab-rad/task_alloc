# Solution is feasible if it scores perfectly on the first four constraints.
def feasible_assignment(problem, assignment):
    scores = subscores(problem, assignment)
    return feasible_score(scores)

def feasible_score(subscores):
    return subscores[0:4] == (1.0, 1.0, 1.0, 1.0)

def all_tasks_assigned(problem, assignment):
    if assignment == None:
        return False
    for task in problem.tasks.values():
        count = 0
        for v in assignment.mapping.keys():
            if v.task == task:
                count += 1
        if count != 1:
            return False
    return True

def subscores(problem, assignment):
    util = calc_util(problem, assignment)
    bandwidth = calc_bandwidth(problem, assignment)
    residency = calc_residency(problem, assignment)
    coresidency = calc_coresidency(problem, assignment)
    qos = calc_qos(problem, assignment)
    spare = calc_free_cycles(problem, assignment)
    return (util, bandwidth, residency, coresidency, qos, spare)


def calc_util(problem, assignment):
    processors = problem.processors
    score = 0
    for p in processors.values():
        usage = assignment.proc_util(p)
        capacity = p.capacity
        if usage <= capacity:
            score += 1.0
        else:
            score += 1.0 - ((usage - capacity) / (capacity*1.0))
    return score / len(processors)


def calc_bandwidth(problem, assignment):
    links = problem.links
    score = 0
    for link in links.values():
        usage = assignment.bandwidth_util(link)
        capacity = link.bandwidth
        if usage <= capacity:
            score += 1.0
        else:
            score += 1.0 - ((usage - capacity) / (capacity*1.0))
    return score / len(links)


def calc_residency(problem, assignment):
    score = 0.0
    for (variant, assigned_processor) in assignment.mapping.items():
        if assigned_processor:
            if variant.residency == [] or assigned_processor in variant.residency:
                score += 1.0
    return score / len(problem.tasks) # not len (variants)


def calc_coresidency(problem, assignment):
    score = 0.0
    for (variant, assigned_processor) in assignment.mapping.items():
        task = variant.task
        satisfied = True
        for cotask in task.coresidence:
            for variant in cotask.variants:
                if variant in assignment.mapping.keys():
                    if assignment.mapping[variant] != assigned_processor:
                        satisfied = False
        if satisfied:
            score += 1.0
    return score / len(problem.tasks)


def calc_qos(problem, assignment):
    qos = 0.0
    for v in assignment.mapping.keys():
        qos += (v.qos / 100.0)
    return qos / len(problem.tasks)


def calc_free_cycles(problem, assignment):
    cycles = 0.0
    total_capacity = 0.0
    for processor in problem.processors.values():
        usage = assignment.proc_util(processor)
        spare = processor.capacity - usage
        if spare > 0:
            cycles += spare
        total_capacity += processor.capacity
    return cycles / total_capacity