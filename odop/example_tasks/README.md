# Example tasks


## Task specification (required for scheduling and execution)

- resources:
    - always:
        - task function name, file name, executable (see below)
        - task id
        - cpu
        - time
        - memory
    - optional:
        - interrupt allowed (default to True)
    - other resources: the resource tracker needs to know about these or the job does not execute
        - network bandwidth
        - gpu
        - list of filenames
        - files in directory, minimum number
        - files in shared memory
        - parameter available
-  dependencies:
    - list of task IDs


### Information required to serialize and 



## Constraints

Option 1: Tasks need to be written as Python functions. To run, we import the file and execute the task. Or we execute a script that does that.

Option 2: Tasks need to be Python scripts. We simply run the file. Could be more complicated with decorators.

Option 3: Serialize the Python function. Limited to standard Python functions, but does not depend on the environment.


