include "globals.mzn";

%
% Instance data
%

int: nTasks;        % Tasks are called 1..nTasks
int: nVariants;     % Variants are called 1..nVariants
int: nProcessors;   % Processing elements are 1..nProcessors

% For each task, say which set of variants are associated with that task. The
% variant sets must be disjoint, and their union must be 1..nVariants.
array[1..nTasks] of set of 1..nVariants: tasksToVariants;

constraint assert (array_union(tasksToVariants) = 1..nVariants,
        "tasksToVariants union is not 1..nVariants");

constraint forall (t in 1..nTasks, u in 1..nTasks where t != u) (
        assert (card(tasksToVariants[t] intersect tasksToVariants[u]) = 0,
            "tasksToVariants are not disjoint"));

% For each variant, its processor utilisation.
array[1..nVariants] of int: utilisations;

% For each variant, its quality of service, QoS
array[1..nVariants] of int: qos;

% For each processor, its capacity.
array[1..nProcessors] of int: capacities;

% For each pair of processors, the link capacity from the first to the second.
% The link capacity from a processor to itself is assumed to be infinite, but
% must be specified as -1 in the input. The capacities must be symmetric.
array[1..nProcessors, 1..nProcessors] of int: links;

constraint forall (p in 1..nProcessors) (assert(links[p, p] == -1,
            "self links must be -1"));

constraint forall (p in 1..nProcessors, q in 1..nProcessors) (
        assert(links[p, q] == links[q, p],
            "links must be symmetric"));

% For each pair of tasks, the bandwidth required between the two tasks. A task
% must not require any bandwidth to itself.
array[1..nTasks, 1..nTasks] of int: bandwidths;

constraint forall (t in 1..nTasks) (assert(bandwidths[t, t] == 0,
            "self bandwidths must be 0"));

%
% Decision variables
%

% We construct a partial mapping from variants to processors. Zero means
% unallocated.
array[1..nVariants] of var 0..nProcessors: assignments;

%
% Ugly hackery
%

% We want to know the bandwidth required between two variants, not two tasks,
% so we reindex the bandwidths array for convenience. Recall that each variant
% belongs to exactly one task, so the [1] hack will work.
array[1..nVariants, 1..nVariants] of int: bandwidthsForVariant = array2d(
        1..nVariants, 1..nVariants, [ bandwidths[
            [ t | t in 1..nTasks, s in tasksToVariants[t] where s == v][1],
            [ t | t in 1..nTasks, s in tasksToVariants[t] where s == w][1]
        ] | v in 1..nVariants, w in 1..nVariants ]);

%
% Constraints
%

% We want to say that exactly one variant of a task is allocated. We do this by
% saying that all but one variant is unallocated, instead.
constraint forall (t in 1..nTasks) (
    exactly(card(tasksToVariants[t]) - 1, [ assignments[v] | v in tasksToVariants[t] ], 0));

% Processor capacity constraints.
constraint forall (p in 1..nProcessors) (
    sum([if assignments[v] == p then utilisations[v] else 0 endif | v in 1..nVariants]) <= capacities[p]);

% Link capacity constraints. We assume infinite link capacity between a
% processor and itself.
constraint forall (l in 1..nProcessors, m in 1..nProcessors where l != m) (
    sum([
        if assignments[v] == l /\ assignments[w] == m then
            bandwidthsForVariant[v, w] + bandwidthsForVariant[w, v]
        else
            0
        endif
        | v in 1..nVariants, w in 1..nVariants]) <= links[l, m]);

% Each variant specifies which processors it may run on. The processor 0
% (meaning unallocated) must always be permitted.
array[1..nVariants] of set of 0..nProcessors: permittedProcessors;

constraint forall (v in 1..nVariants) (assert(0 in permittedProcessors[v],
           "processor 0 must always be permitted"));

% Each variant can only be run on a permitted processor.
constraint forall (v in 1..nVariants) (assignments[v] in permittedProcessors[v]);

% Some tasks must be run on the same processor.
array[int] of set of 1..nTasks: sameProcessor;

% Some sets of tasks must be run on the same processor.
constraint forall (s in sameProcessor, t in s, u in s, a in tasksToVariants[t], b in tasksToVariants[u] where a != b) (
   assignments[a] != 0 /\ assignments[b] != 0 -> assignments[a] = assignments[b]);

% QOS Goal -- this is for the second pass.
 int: qosGoal;
  constraint sum([if assignments[v] != 0 then qos[v] else 0 endif | v in 1..nVariants]) = qosGoal;


%
% Objective
%

% min
var int: util_objective = sum([if assignments[v] != 0 then utilisations[v] else 0 endif | v in 1..nVariants]);

% maximise this
%var float: qos_objective = sum([if assignments[v] != 0 then qos[v] else 0 endif | v in 1..nVariants]);

solve minimize(util_objective);

output ["objective = " ++ show(util_objective) ++ "\n" ++ "assignments = " ++ show(assignments)];

