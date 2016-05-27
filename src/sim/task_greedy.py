__author__ = 'whited'
import task_model as model
TASK_FILE = '../../scenarios/simple_task.graphml'
PROCESSOR_FILE = '../../scenarios/simple_processors.graphml'

def solve(problem):
    tasks = tasks_by_max_size(problem)
    processors = processors_by_capacity(problem)
    assignment = model.Assignment()

		# First step: allocate weakest variant of tasks with residence constraint
    for t in tasks:
        variants = sorted(t.variants, key=lambda v: v.size, reverse=False)
        				
        for v in variants:
            if v.residency != []:
                if not assignment.which_variant(t):
                    for p in processors:                                    
                        if p in v.residency:
                            if not assignment.which_variant(t):
                                if feasible(v, p, assignment, problem):                              
                                    assignment.assign(v,p)                                     

    # Second step: allocate weakest variant of tasks with coresidence constraint
    for t in tasks:
        if not assignment.which_variant(t):            
            variants = sorted(t.variants, key=lambda v: v.size, reverse=False)
        				
            for v in variants:
                if v.task.coresidence != []:                                    
                    for p in processors:                    
                        if not assignment.which_variant(t):                                   
                            if feasible_with_cores(v, p, assignment, problem):
                                assignment.assign(v,p)                             
                                                                                                                                                
    # Third step: allocate weakest variant of other tasks
    for t in tasks:
        if not assignment.which_variant(t):
            variants = sorted(t.variants, key=lambda v: v.size, reverse=False)
        
            for v in variants:
                for p in processors:
                    if not assignment.which_variant(t):
                        if feasible(v, p, assignment, problem):
                            assignment.assign(v,p)                                 

    # Fourth step: replace weakest variant allocated by a more powerful one, if possible
    for t in tasks:
        #variants = sorted(t.variants, key=lambda v: v.size, reverse=True)
        variants = sorted(t.variants, key=lambda v: v.size, reverse=False)	# there are 2 options, but this one provides better results

        if len(variants) > 1:
            reasigned = False
            for v in variants:
                if not reasigned:                             
                    if assignment.which_variant(t) != v:
                        p = assignment.processor_for_task(t)
                        if v.size + assignment.proc_util(p) - variants[0].size <= p.capacity:                                                        
                        #if v.size + assignment.proc_util(p) - variants[len(variants)-1].size <= p.capacity:                            
                            assignment.remove(variants[0])
                            #assignment.remove(variants[len(variants)-1])
                            assignment.assign(v,p)
                            reasigned = True

    return assignment


def tasks_by_max_size(problem):
    return sorted(problem.tasks.values(), key=lambda task: max([v.size for v in task.variants]), reverse=True)


def processors_by_capacity(problem):
    return sorted(problem.processors.values(), key=lambda p: p.capacity, reverse=True)


def feasible(v, p, assignment, problem):
   
    # Don't overload
    if v.size + assignment.proc_util(p) > p.capacity:
        return False
   
    # Bandwidth
    tmp_assignment = assignment.clone()
    tmp_assignment.assign(v, p)
    for link in problem.links.values():
        if tmp_assignment.bandwidth_util(link) > link.bandwidth:
            return False

    return True


def feasible_with_cores(v, p, assignment, problem):   

    # Don't overload
    if v.size + assignment.proc_util(p) > p.capacity:
        return False

    # Coresidency
    for other_task in v.task.coresidence:
        if assignment.which_variant(other_task):
            if assignment.processor_for_task(other_task) != p:
                return False
    
    # Bandwidth
    tmp_assignment = assignment.clone()
    tmp_assignment.assign(v, p)
    for link in problem.links.values():
        if tmp_assignment.bandwidth_util(link) > link.bandwidth:
            return False

    return True

