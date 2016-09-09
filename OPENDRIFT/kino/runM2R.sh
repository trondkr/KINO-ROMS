#!/bin/bash
#
#  Give the job a name
#PBS -N "opendrift_KINO"
#
#  Specify the project the job belongs to
#PBS -A imr
#PBS -q normal
#PBS -l mppwidth=1,walltime=96:00:00
#PBS -l mppmem=2000MB
#PBS -l mppnppn=16
#
#  Send me an email on  a=abort, b=begin, e=end
#PBS -m abe
#
#  Use this email address (check that it is correct):
#PBS -M trond.kristiansen@imr.no
#
#  Write the standard output of the job to file 'mpijob.out' (optional)
#PBS -o  opendrift_KINO.out
#
#  Write the standard error of the job to file 'mpijob.err' (optional)
#PBS -e  opendrift_KINO.err
#

#  Make sure I am in the correct directory
cd /work/shared/imr/KINO/OPENDRIFT
module load python

export MPLCONFIGDIR=${pwd}
export TMP=`pwd`
export PYTHON_EGG_CACHE=/work/shared/imr/KINO/OPENDRIFT

aprun -B python kino.py > opendrift.log