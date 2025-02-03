# Scheduling Algorithms

By default, Odop uses a priority first scheduling algorithm, that tries to fit
the highest priority task into the available resources. The algorithm can be
set in the runtime configuration file (`odop_conf.yaml`) in the `examples`
directory.

The following scheduling algorithms included with Odop:
 - `priority`: The default algorithm. Prioritizes tasks based on the priority
   parameter.
 - `fifo`: First in, first out. Tasks are run in the order they are added to
    the queue.
 - `round_robin`: Assigns tasks to nodes in a round-robin fashion. Tasks are
    ordered by priority, as in the default case, but not necessarily run in
    that order.
 - `best_fit`: Assigns the largest tasks first.

