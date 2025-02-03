odop tasks to run:

reduce.py  
to run reduce.py  
 module load cray-hdf5
python(3) reduce.py

> **_NOTE:_**  
> PC python call MPI init a lot so we need to remove it in order to be able to run only one

upload.py  
to run upload.py do the following:  
 module load python-data/(LUMI)cray-python  
 (LUMI) module use /appl/local/csc/modulefiles  
 module load allas  
 allas-conf and choose project_2000403 Magneto-helioseismology in conjunction with dynamo simulations (international use)  
 python(3) upload.py
