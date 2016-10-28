
"""
This script is used to plot the RegScen Arctic grid

"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from pylab import *
from netCDF4 import Dataset
import datetime
from shutil import copyfile
import glob, os
import subprocess

__author__   = 'Trond Kristiansen'
__email__    = 'me (at) trondkristiansen.com'
__created__  = datetime.datetime(2016, 8, 25)
__modified__ = datetime.datetime(2016, 8, 25)
__version__  = "1.0"
__status__   = "Development, 25.8.2016"



"""" ------------------------------------------------------------------
     MAIN
     Trond Kristiansen, 25.8.2016
     
     ------------------------------------------------------------------
"""

doc="""This script plots the RegScen currents on a map
"""

years=[2012,2013]

for year in years:

  if year==2013:

    datesToFind=[datetime.datetime(year,1,1,10,30,05),
    datetime.datetime(year,4,1,10,30,05),
    datetime.datetime(year,7,1,10,30,05),
    datetime.datetime(year,10,1,10,30,05)]

  if year==2011:
  
    datesToFind=[datetime.datetime(year,1,1,12,03,35),
    datetime.datetime(year,4,1,12,03,35),
    datetime.datetime(year,7,1,12,03,35),
    datetime.datetime(year,10,1,12,03,35)]

  if year==2012:
  
    datesToFind=[datetime.datetime(year,1,1,10,30,05),
    datetime.datetime(year,4,1,10,30,05),
    datetime.datetime(year,7,1,10,30,05),
    datetime.datetime(year,10,1,10,30,05)]


  DOWNLOADS="/work/users/trondk/KINO/FORWARD/Run/RESULTS/DOWNLOADS/"
  os.chdir("/work/users/trondk/KINO/FORWARD/Run/RESULTS/%s"%(year))
  allfiles=glob.glob("*.nc")
  allfiles.sort()
  for infile in allfiles:
    
    myCDF=Dataset(infile)
    timeR=np.asarray(myCDF.variables["ocean_time"][:])
    refDateR=datetime.datetime(1948,1,1,0,0,0)

    for mytimeindex in xrange(len(timeR)):
        myseconds=int(timeR[mytimeindex])
        current=refDateR + datetime.timedelta(seconds=myseconds)
       # print "=> %s"%(current)
        if current in datesToFind:
          print "==> Found timestep that is required: %s in file %s"%(current,infile)

          outfile=DOWNLOADS+infile
          command="ncks -d ocean_time,4,4 -v salt,temp,lon_rho,lat_rho,u,v %s %s"%(infile,outfile)
          process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
          process.wait()
      
          print "==> Copied file... %s success: %s"%(DOWNLOADS+infile,process.returncode)
    myCDF.close()
