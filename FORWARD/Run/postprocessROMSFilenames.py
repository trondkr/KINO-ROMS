import os, shutil
import datetime as datetime
from netCDF4 import Dataset
import numpy as np
import glob
import string

__author__   = 'Trond Kristiansen'
__email__    = 'me (at) trondkristiansen.com'
__created__  = datetime.datetime(2015, 10, 5)
__modified__ = datetime.datetime(2015, 10, 5)
__version__  = "1.0"
__status__   = "Production"

"""This script takes the output of running ROMS where the name of result files are an increasing integer ROMS.1, ROMS.2, 
ROMS.3 ... ROMS.N. The new filenames uses the startdate (ocean_time ) of the ROMS file as the integer instead. 
This means that all files have names indicating start date as days since 1948/1/1. """

def extractTimeFromNetCDF(infile):

	cdf = Dataset(infile)
	times = cdf.variables["ocean_time"][:]
	refDate=datetime.datetime(1948, 1, 1, 0, 0, 0)
  	currentDate=refDate + datetime.timedelta(seconds=times[0])
  	print "time-step: %s - %s" % (times[0], currentDate)
  	difference = currentDate - refDate
  	print "Days since refdate %s - %s"%(refDate,difference.days)
  	return difference.days

def renameROMSFiles(datapath,mypattern,outputDirectory,newFilename):

	counter=0
	argument="%s%s"%(datapath,mypattern)
	allFiles = glob.glob(argument)
	allFiles.sort()
		
	print "argument %s"%(argument)
	print "Sorting %s files found in NS8KM datadirectory"%(len(allFiles))

	for resultfile in allFiles:

		days = extractTimeFromNetCDF(resultfile)

		newName = "%s%s_%s.nc"%(outputDirectory,newFilename,days)
		shutil.move(resultfile,newName)

		print "File %s renamed to %s"%(resultfile,newName)

def main():

	# Where the ROMS results files are stored
	datapath ="/work/users/trondk/KINO/FORWARD/Run/SAVE/"
	# The pattern of the ROMS files
	mypattern="ocean_avg_*.nc"
	# The directory to store the renamed files
	outputDirectory="/work/users/trondk/KINO/FORWARD/Run/RESULTS/"
	# The new filename pattern where days since 1948/1/1 will be added at the end: kino_1600m_29765.nc
	newFilename="kino_1600m"

	# Create results folder  
	if not os.path.exists(outputDirectory):
		os.makedirs(outputDirectory)

	# Rename all of the files in the datatpath 
	renameROMSFiles(datapath,mypattern,outputDirectory,newFilename)

if __name__ == "__main__":
	main()

