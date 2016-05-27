from task_model import Assignment
import task_score as score
import random
verbose = True


class LocalSearch():

    def __init__(self, problem):
        self.problem = problem
        self.current = None
        self.best_assignment = None
        self.best_score = None
        self.evals = None
        self.step = None

    def initialise(self):
        self.randomise()
        self.current_score = score.subscores(self.problem, self.current)
        self.best_assignment = self.current
        self.best_score = self.current_score
        self.evals = 1
        self.step = 1

    def log(self, restart=False):
        if restart:
            restart_msg = '[RESTART]'
        else:
            restart_msg = ''
        if verbose:
            print restart_msg + str(self.step) + ' Current: ' + str(self.current_score)

    def solve(self):
        self.initialise()
        while True:
            self.log()
            self.step += 1
            self.gen_neighbours()
            better = self.try_moving()
            if not better:
                self.restart()

    def restart(self):
        self.randomise()
        self.current_score = score.subscores(self.problem, self.current)
        if self.current_score > self.best_score:
            self.best_score = self.current_score
            self.best_assignment= self.current
        if verbose:
            self.log(True)

    def eval(self, assignment):
        self.evals += 1
        return score.subscores(self.problem, assignment)

    def try_moving(self):
        for n in self.neighbours:
            n_scores = self.eval(n)
            if n_scores > self.best_score:
                self.best_assignment = n
                self.best_score = n_scores
            if n_scores > self.current_score:
                self.current = n
                self.current_score = n_scores
                return True
        return False


    def gen_neighbours(self):
        self.neighbours = []
        # Move variant to another processor
        for task in self.problem.tasks.values():
            variant = self.current.which_variant(task)
            processors = list(self.problem.processors.values())
            processors.remove(self.current.mapping[variant])
            for p in processors:
                new_assignment = self.current.clone()
                new_assignment.assign(variant, p)
                self.neighbours.append(new_assignment)
        # Change the variant
        for task in self.problem.tasks.values():
            variant = self.current.which_variant(task)
            processor = self.current.mapping[variant]
            variants = list(task.variants)
            variants.remove(variant)
            for v in variants:
                new_assignment = self.current.clone()
                new_assignment.remove(variant)
                new_assignment.assign(variant, processor)
                self.neighbours.append(new_assignment)

    def randomise(self):
        self.current = Assignment()
        for task in self.problem.tasks.values():
            variant = random.choice(task.variants)
            processor = random.choice(self.problem.processors.values())
            self.current.assign(variant, processor)

