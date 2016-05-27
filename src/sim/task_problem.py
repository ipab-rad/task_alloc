import task_model as model

TASKS_PER_ROBOT = 6			  	# fixed parameter (initially)
VARIANTS_PER_ROBOT = 12			# fixed parameter (initially)
VARIANTS_PER_CAMERA = 4			# fixed parameter (initially)

ROBOT_CPU_CAPACITY = 100
SERVER_FACTOR = 4


def generate(num_processors, num_robots, num_cameras):
    msgs_robot = 0
    for x in range(1, num_robots + 1):
        msgs_robot += 8 + num_robots - x

    # Processors for each robot
    processors = {}
    for x in range(1, num_robots+1):
        p = model.Processor('P' + str(x), ROBOT_CPU_CAPACITY)
        processors[p.id] = p

    # Processors for servers
    for x in range(num_robots+1, num_processors+1):
        capacity = ROBOT_CPU_CAPACITY*SERVER_FACTOR
        p = model.Processor('P' + str(x), capacity)
        processors[p.id] = p

    # Links
    num_wireless_links = 0
    for x in range(1, num_robots+1):
        num_wireless_links += num_processors - x

    num_link=1
    links = {}

    # wireless links
    for x in range(1, num_robots+1):
        for y in range(x+1, num_processors+1):
            bandwidth = 54000/num_wireless_links # integer division as minizinc needs it
            link = model.Link('L' + str(num_link), processors['P'+str(x)], processors['P' + str(y)], bandwidth)
            links[link.id] = link
            processors['P'+str(x)].add_link(link)
            processors['P'+str(y)].add_link(link)
            num_link+=1

    # wired links
    for x in range(num_robots+1, num_processors+1):
        for y in range(x+1, num_processors+1):
            bandwidth = 100000
            link = model.Link('L' + str(num_link), processors['P'+str(x)], processors['P'+str(y)], bandwidth)
            links[link.id] = link
            processors['P'+str(x)].add_link(link)
            processors['P'+str(y)].add_link(link)
            num_link+=1


    # TASKS:
    #  Experiment, T1
    #  Tracker (one per camera), T2..T(1+camera_no)
    #  Then for each robot:
    #       Environment (1+cameras) + (robot-1)*6
    #       Model,
    #       Planner,
    #       AMCL,
    #       Navigation,
    #       Youbot_core

    if num_processors - num_robots > 1:
        servers_residence = []
        for n in range(num_robots+1, num_processors+1):
            servers_residence.append(processors['P' + str(n)])
    else:
        servers_residence = [processors['P' + str(num_processors)]]

    num_task = 1
    tasks = {}

    # Experiment task
    id = 'T' + str(num_task)
    task = model.Task(id, [], None)
    variant = model.Variant(task, 1, 1, servers_residence, 'V1')
    task.variants = [variant]
    tasks[task.id] = task
    num_task += 1


    # Tasks for cameras
    for x in range(1, num_cameras+1):
        # Tracker
        id = 'T' + str(num_task)
        task = model.Task(id, [], None)
        variant1 = model.Variant(task, 200, 100, servers_residence, 'V1')
        variant2 = model.Variant(task, 160, 90, servers_residence, 'V2')
        variant3 = model.Variant(task, 120, 70, servers_residence, 'V3')
        variant4 = model.Variant(task, 80, 40, servers_residence, 'V4')
        task.variants = [variant1, variant2, variant3, variant4]
        tasks[task.id] = task
        num_task += 1


    # Tasks for robots
    for x in range(1, num_robots+1):

        robot_residence = []
        robot_residence.append(processors['P' + str(x)])
    
        # Environment
        id = 'T' + str(num_task)
        task = model.Task(id, [], None)
        variant1 = model.Variant(task, 1, 1, [], 'V1')
        task.variants = [variant1]
        tasks[task.id] = task
        num_task += 1

        # Model
        id = 'T' + str(num_task)
        task = model.Task(id, [], None)
        variant1 = model.Variant(task, 59, 100, [], 'V1')
        variant2 = model.Variant(task, 39, 70, [], 'V2')
        variant3 = model.Variant(task, 17, 20, [], 'V3')
        task.variants = [variant1, variant2, variant3]
        tasks[task.id] = task
        num_task += 1
      
        # Planner
        id = 'T' + str(num_task)
        planner_task = model.Task(id, [], None)
        variant1 = model.Variant(planner_task, 1, 1, [], 'V1')
        planner_task.variants = [variant1]
        tasks[planner_task.id] = planner_task
        num_task += 1     

        # AMCL
        id = 'T' + str(num_task)
        task = model.Task(id, [], None)
        variant1 = model.Variant(task, 66, 100, [], 'V1')
        variant2 = model.Variant(task, 41, 50, [], 'V2')
        variant3 = model.Variant(task, 19, 20, [], 'V3')
        task.variants = [variant1, variant2, variant3]
        tasks[task.id] = task
        num_task += 1

        # Navigation
        id = 'T' + str(num_task)
        navigation_task = model.Task(id, [], None)
        variant1 = model.Variant(navigation_task, 50, 100, [], 'V1')
        variant2 = model.Variant(navigation_task, 39, 65, [], 'V2')
        variant3 = model.Variant(navigation_task, 25, 10, [], 'V3')
        navigation_task.variants = [variant1, variant2, variant3]
        tasks[navigation_task.id] = navigation_task
        num_task += 1
        
        # Youbot_core
        id = 'T' + str(num_task)
        youbot_task = model.Task(id, [], None)
        variant1 = model.Variant(youbot_task, 16, 1, robot_residence, 'V1')
        youbot_task.variants = [variant1]
        tasks[youbot_task.id] = youbot_task
        num_task += 1

        # two coresidence constraints
        # Planner with Navigation
        planner_coresidence = tasks['T' + str(1+num_cameras+((x-1)*TASKS_PER_ROBOT)+5)]
        planner_task.coresidence = [planner_coresidence]
        # Navigation with planner
        navigation_coresidence = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+3)]
        navigation_task.coresidence = [navigation_coresidence]
      
    # Messages

    num_mess=1
    messages = {}

    # Messages from Experiment (Experiment - Environment)
    for x in range(1, num_robots+1):
        msg_id = 'M' + str(num_mess)
        source = tasks['T1']
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+1)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

    # Messages from cameras (Tracker - Environment)
    for x in range(1, num_cameras+1):
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+x)]
        target = tasks['T' + str(2+num_cameras)]
        size = 3
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

    # Messages from robots
    for x in range(1, num_robots+1):
        # (Environment - Model)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+1)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+2)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # (Environment - Planner)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+1)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+3)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # (Environment - Youbot_core)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+1)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+6)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # Between robots (Environment - Environment)
        for y in range(x+1, num_robots+1):
            msg_id = 'M' + str(num_mess)
            source = tasks['T' + str(1+(num_cameras)+(x-1)*TASKS_PER_ROBOT+1)]
            target = tasks['T' + str(1+(num_cameras)+(y-1)*TASKS_PER_ROBOT+1)]
            size = 1
            message = model.Message(msg_id, source, target, size)
            source.add_msg_source(message)
            target.add_msg_sink(message)
            num_mess += 1
            messages[message.id] = message

        ##
       
        # (Planner - Navigation)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+3)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+5)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # (Navigation - Environment)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+5)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+1)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # (Youbot_core - Navigation)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+6)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+5)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # (Youbot_core - AMCL)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+6)]
        target = tasks['T' + str(1+num_cameras+(x-1)*TASKS_PER_ROBOT+4)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message

        # (AMCL - Environment)
        msg_id = 'M' + str(num_mess)
        source = tasks['T' + str(1+(num_cameras)+(x-1)*TASKS_PER_ROBOT+4)]
        target = tasks['T' + str(1+(num_cameras)+(x-1)*TASKS_PER_ROBOT+1)]
        size = 1
        message = model.Message(msg_id, source, target, size)
        source.add_msg_source(message)
        target.add_msg_sink(message)
        num_mess += 1
        messages[message.id] = message
              

    problem = model.TaskProblem(tasks=tasks, messages=messages, processors=processors, links=links)
    return problem


if __name__ == '__main__':
    processors = 2
    robots = 1
    cameras = 1
    problem = generate(processors, robots, cameras)
    print problem

