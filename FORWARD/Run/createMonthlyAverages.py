
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
monthsToFind=[1,4,7,10]

for year in years:

  TEMP="/work/users/trondk/KINO/FORWARD/Run/RESULTS/DOWNLOADS/TEMP/"
  DOWNLOADS="/work/users/trondk/KINO/FORWARD/Run/RESULTS/DOWNLOADS/"
  os.chdir("/work/users/trondk/KINO/FORWARD/Run/RESULTS/%s"%(year))
  allfiles=glob.glob("*.nc")
  allfiles.sort()

  for month in monthsToFind:

    # Remove temporary files
    tempfiles = glob.glob(TEMP+'*')
    for f in tempfiles:
      print "Removing file %s in folder %s"%(f,TEMP)
      os.remove(f)

    filesToAverage=[]
    for infile in allfiles:
    #  print "Examining file %s"%(infile)
      myCDF=Dataset(infile)
      timeR=np.asarray(myCDF.variables["ocean_time"][:])
      refDateR=datetime.datetime(1948,1,1,0,0,0)

      for mytimeindex in xrange(1):
          myseconds=int(timeR[mytimeindex])
          current=refDateR + datetime.timedelta(seconds=myseconds)
     #     print "=> %s"%(current)

          if int(current.month) == int(month) and int(current.year)==int(year):
            print "=> Found file that will be included for month %s: %s in file %s"%(month,current,infile)
            filesToAverage.append(infile)

            command="ncks -d ocean_time,4,4 -v salt,temp,lon_rho,lat_rho,u,v %s %s"%(infile,TEMP+infile)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            process.wait()

      myCDF.close()

    print "Starting averaging %s files for month %s and year %s"%(len(filesToAverage),month,year)
    outfile=DOWNLOADS+'average_month_%s_year_%s.nc'%(month,year)
    command="cdo ensmean %s %s"%(TEMP+'*',outfile)
    print "Running command: %s"%(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
        
    print "Averaged file... %s success: %s"%(outfile,process.returncode)
      