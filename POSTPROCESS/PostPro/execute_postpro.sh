#!/bin/bash
#
# Information for script ROMS_postpro.sh is set here.
#
# Decide whether you will run this script interactively (=0) or as a batch job (=1)
# NB: If you apply the switch "roms2z", you should run this script as a batch job.
batch=1
#
# Define which variables you want to extract from the model files
out_zeta=1           # Switch to define if sea surface elevation is written to z/s-level-file (=1) or not (=0)
out_fluxes=1         # Switch to define if surface net heat and salt flux is written to z/s-level-file (=1) or not (=0)
out_curr=1           # Switch to define if currents (x- and y-component) is written to z/s-level-file (=1) or not (=0)
out_curr_rot=0       # Switch to define if currents (rotated eastward and northward internally in ROMS) is written to z-level-file (=1) or not (=0)
out_curr_polar=0     # Switch to define if currents (polar coord.) is written to z-level-file (=1) or not (=0)
out_salt=1           # Switch to define if salinity is written to z/s-level-file (=1) or not (=0)
out_temp=1           # Switch to define if temperature is written to z/s-level-file (=1) or not (=0)
#
# Name of experiment (only used in output filenames)
exp='kino_1600m'
#
# List which z-levels you want to interpolate results to (nonnegative numbers, floating numbers allowed)
out_zlevels="0 3 5 10 15 20 30 50 75 100 125 150 200 250 300 400 500 600 700 800 900 1000 1250 1500 1750 2000 2250 2500 2750 3000"

#
# List ONE s-level you want to extract results from (numbers between 1 (bottom) and Nvert (surface).
# NB: Nvert is not defined here, see size of Nvert in e.g. NorKyst-800m/execute_script.sh or size of N when ncdump'ing one of the ROMS files.
# NB: If you want several s-levels, run this script one time for each output s-level.
out_slevel=1
#
# After interpolation to A-grid and z-levels or s-level only, hyperslap to this subdomain to reduce storage
# (refers to actual model grid, not the entire ROMS grid)
# x1 and y1 must not exceed Lm, Mm, i.e., no. of I/J-direction interior RHO-points
x0=10; x1=560
y0=10; y1=490
#
# Split area when calculating min, max and std fields is perhaps necessary due to memory limitations
# Tip: Start with nsplitarea=1, then increase value one-by-one if you receive an error message from the ncwa-command
# Tip2: If problems with memory restrictions, run script with roms2z=1 and roms2s=1, then turn these off and run filestat_z/s
# for smaller sub-domains, controlled by x0, x1, y0 and y1.
nsplitarea=1
#
# Set path to ROMS output files, typically named norkyst_800m_his_????.nc, norkyst_800m_avg_????.nc, norkyst_800m_his.nc_* or norkyst_800m_avg.nc_*
BASE=`pwd`
RDIR=${BASE}/Files4Stat  # Make soft links or copy ROMS files to this directory. All files will be read.
#
# Set the name of your machine. Available: hexagon
#
machine=hexagon
#
# Switches (for full post-processing, set all to 1, otherwise apply each individually)
#
roms2z=1             # Switch to run program that interpolates model results to A-grid and z-levels (=1) or not (=0)
roms2s=0             # Switch to extract fields on a certain s-level (=1) or not (=0)
filestat_z=0         # Switch to generate mean, min, max, rms and std fields from chosen z-levels  (=1) or not (=0)
filestat_s=0         # Switch to generate mean, min, max, rms and std fields from chosen s-level (=1) or not (=0)
#
# DO NOT CHANGE ...
#
# Send statements to a temporary ascii-file that will be read by ROMS_postpro.sh (or ROMS_postpro.job)
#
echo ${out_zeta} ${out_fluxes} ${out_curr} ${out_curr_rot} ${out_curr_polar} ${out_salt} ${out_temp} \
     ${out_slevel}                                                                                   \
     ${exp}                                                                                          \
     ${x0} ${x1} ${y0} ${y1}                                                                         \
     ${nsplitarea}                                                                                   \
     ${RDIR} ${machine}                                                                              \
     ${roms2z} ${roms2s} ${filestat_z} ${filestat_s}                                                 \
     ${out_zlevels}                                                                                  > ./roms_ptmp.in
#
# Execute main-script
#
if [ ${batch} -eq 1 ]; then
  echo
  echo "You must send ROMS_postpro.job to batch queue. Make sure that heading suits your account AND that path (BASE) is correct."
  echo "Then you must put the job-script to queue yourself: qsub ROMS_postpro.job"
  echo
else
  #nohup ./ROMS_postpro.sh ./roms_ptmp.in &  # Use this command line if you want to log out after execution
  ./ROMS_postpro.sh ./roms_ptmp.in
fi
#
exit
#

