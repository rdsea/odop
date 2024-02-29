# Example tasks

### Information required to schedule tasks

- resources:
    - always:
        - task function name, file name, executable (see below)
        - cpu
        - time
        - memory
    - other resources: the resource tracker needs to know about these or the job does not execute
        - filename
        - network bandwith
        - gpu
    -  dependencies:
        - depends on (executes only after task)

## Constraints

Option 1: Tasks need to be written as Python functions. To run, we import the file and execute the task. Or we execute a script that does that.

Option 2: Tasks need to be Python scripts. We simply run the file. Could be more complicated with decorators.

