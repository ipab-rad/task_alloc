class TaskProblem():
    def __init__(self, tasks, messages, processors, links):
        self.processors = processors
        self.links = links
        self.tasks = tasks
        self.messages = messages

    def __str__(self):
        res = describe('Tasks', self.tasks)
        res += describe('Messages', self.messages)
        res += describe('Processors', self.processors)
        res += describe('Links', self.links)
        return res

    def sorted_tasks(self):
        s_tasks = []
        for i in range(1, len(self.tasks)+1):
            s_tasks.append(self.tasks['T' + str(i)])
        return s_tasks

    def sorted_processors(self):
        s_processors = []
        for i in range(1, len(self.processors)+1):
            s_processors.append(self.processors['P' + str(i)])
        return s_processors

    def sum_messages(self, task1, task2):
        total = 0
        for message in self.messages.values():
            if (message.from_task == task1 and message.to_task == task2):
                total += message.size
        return total

    def processor(self, p_id):
        return self.processors['P' + str(p_id)]

    def variant(self, v_id):
        current_id = 1
        for t in self.sorted_tasks():
            for v in t.variants:
                if current_id == v_id:
                    return v
                current_id += 1
        raise Exception('Unexpected variant id: ' + str(v_id))



class Assignment():
    def __init__(self):
        self.mapping = {}

    def clone(self):
        a = Assignment()
        for (variant, processor) in self.mapping.items():
            a.assign(variant, processor)
        return a

    def __str__(self):
        solution = []
        for (variant, processor) in self.mapping.items():
            solution.append((str(variant), processor.id))
        sorted_solution = sorted(solution, key=lambda tup: tup[0])
        return str(sorted_solution)

    def long_desc(self):
        solution = []
        for (variant, processor) in self.mapping.items():
            line = (variant.task.id, variant.v_index, processor.id, '##' + str(variant))
            solution.append(line)
        sorted_solution = sorted(solution, key=lambda tup: int(tup[0][1:]))
        desc = ''
        for s in sorted_solution:
            desc += s[0] + ':' + s[1] + ':' + s[2] + '\t\t' + s[3] + '\n'
        return desc

    def assign(self, variant, processor):
        self.mapping[variant] = processor

    def remove(self, variant):
        del self.mapping[variant]

    def proc_util(self, processor):
        util = 0
        for (variant, p) in self.mapping.items():
            if p == processor:
                util += variant.size
        return util

    def qos(self):
        q = 0
        for (variant, _) in self.mapping:
            q += variant.qos
        return q

    def which_variant(self, t):
        for (v, _) in self.mapping.items():
            if v.task == t:
                return v
        return None

    def processor_for_task(self, t):
        v = self.which_variant(t)
        return self.mapping[v]

    def bandwidth_util(self, link):
        total = 0
        (p1, p2) = link.processors
        p1_tasks = []
        p2_tasks = []
        for variant, allocated_processor in self.mapping.items():
            if allocated_processor == p1:
                p1_tasks.append(variant.task)
            if allocated_processor == p2:
                p2_tasks.append(variant.task)
        for task in p1_tasks:
            for message in task.from_messages:
                if message.to_task in p2_tasks:
                    total += message.size
            for message in task.to_messages:
                if message.from_task in p2_tasks:
                    total += message.size
        return total


class Processor():
    def __init__(self, id, capacity):
        self.id = id
        self.capacity = capacity
        self.links = []

    def __str__(self):
        return self.id + ' (' + str(self.capacity) + ')'

    def add_link(self, link):
        self.links.append(link)

    def bandwidth_to(self, p2):
        bandwidth = 0
        for link in self.links:
            if p2 in link.processors:
                bandwidth += link.bandwidth
        return bandwidth



class Task():
    def __init__(self, id, coresidence, variants):
        self.id = id
        self.coresidence = coresidence
        self.from_messages = []
        self.to_messages = []
        self.variants = variants

    def add_msg_source(self, msg):
        self.from_messages.append(msg)

    def add_msg_sink(self, msg):
        self.to_messages.append(msg)

    def __str__(self):
        variant_desc = map(str, self.variants)
        if self.coresidence != []:
            coresidency_desc = ' Coresidency: ' + '/'.join([task.id for task in self.coresidence])
        else:
            coresidency_desc = ''
        return "Task " + str(self.id) + coresidency_desc + ' Variants: ' + str(variant_desc)

    def sorted_variants(self):
        return sorted(self.variants, key=lambda v: int(v.v_index[1:]))



class Variant():
    def __init__(self, task, size, qos, residency, v_index):
        self.task = task
        self.size = size
        self.qos = qos
        self.residency = residency
        self.v_index = v_index

    def __str__(self):
        return str(self.task.id) + '-Q' + str(self.qos) + '-U' + str(self.size) + '-R:' + ':'.join( [x.id for x in self.residency])


class Message():
    def __init__(self, id, task1, task2, size):
        self.id = id
        self.from_task = task1
        self.to_task = task2
        self.size = size

    def __str__(self):
        return "Message " + str(self.id) + " " + str(self.from_task.id) + " -> " + str(self.to_task.id) + ' [' + str(self.size) + ']'


class Link():
    def __init__(self, id, p1, p2, bandwidth):
        self.id = id
        self.processors = [p1, p2]
        self.bandwidth = bandwidth

    def __str__(self):
        proc_desc = [str(p.id) for p in self.processors]
        return "Link " + str(self.id) + ' ' + str(proc_desc) + ' (' + str(self.bandwidth) + ')'


def describe(header, dict):
    sorted_keys = sorted(dict)
    dict_desc = [str(dict[k]) for k in sorted_keys]
    return header + '\n' + '\n'.join(dict_desc) + '\n'