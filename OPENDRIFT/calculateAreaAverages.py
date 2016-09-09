# coding=utf-8

import os, sys
import numpy as np
import glob
import string
from matplotlib.pyplot import cm 
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from pylab import *
import datetime
from pprint import pprint
from netCDF4 import Dataset, datetime, date2num,num2date

__author__   = 'Trond Kristiansen'
__email__    = 'me (at) trondkristiansen.com'
__created__  = datetime(2016, 8, 10)
__modified__ = datetime(2016, 8, 10)
__version__  = "1.0"
__status__   = "Production"

# --------
# calculateaverages.py
#
# This script takes the output from opendrift and calculates area averages 
# as a function of time. The total area around North Sea is divided into
# bins of specific resolution and the number of particles within each bin 
# is summed for a specific time period (e.g. 1 month). The total output 
# is a heatmap of where the most particles reside for each time period.
# --------

def createBins():

	print 'func: createBins() => Creating bins for averaging'
	xmin=-4.0; xmax=13.0
	ymin=56.0; ymax=62.0
	requiredResolution = 20 # km between each binned box

	deg2rad=np.pi/180.
	R = 6371  # radius of the earth in km
	# Distance from minimum to maximim longitude
	x = (xmax*deg2rad - xmin*deg2rad) * cos( 0.5*(ymax*deg2rad+ymax*deg2rad) )
	y =  ymax*deg2rad - ymax*deg2rad
	dx = R * sqrt( x*x + y*y )
	print "Distance from minimum to maximim longitude binned area is %s km"%(dx)

	# Distance from minimum to maximim latitude
	x = (xmax*deg2rad - xmax*deg2rad) * cos( 0.5*(ymax*deg2rad+ymin*deg2rad) )
	y =  ymax*deg2rad - ymin*deg2rad
	dy = R * sqrt( x*x + y*y )

	print "Distance from minimum to maximim latitude binned area is %s km"%(dy)


	ngridx = int(np.round(dx/requiredResolution,0))
	ngridy = int(np.round(dy/requiredResolution,0))
	
	xi = np.linspace(np.floor(xmin),np.ceil(xmax),ngridx)
	yi = np.linspace(np.floor(ymin),np.ceil(ymax),ngridy)

	print '=> created binned array of domain of size (%s,%s) with resolution %s\n'%(ngridx,ngridy,requiredResolution)

	return xi,yi

def calculateAreaAverages(xi,yi,cdf):

	print 'func: calculateAreaAverages() => Calculating averages within bins'
	print '=> binned domain (%2.1f,%2.1f) to (%2.1f,%2.1f)'%(np.min(xi),np.min(yi),np.max(xi),np.max(yi))

	timesteps = cdf.variables['time'][:]
 	timeunits = cdf.variables["time"].units

	print '=> found %s timesteps in input file'%(len(timesteps))

	for tindex, t in enumerate(timesteps): 

 		currentDate = num2date(t, units=timeunits, calendar="gregorian")
		print '=> Current timestep %s'%(currentDate)

		Xpos = cdf.variables['lon'][:,tindex]
		Ypos = cdf.variables['lat'][:,tindex]
		
		H, xedges, yedges = np.histogram2d(Xpos, Ypos, bins=(xi, yi), normed=False)
		print tindex
		if (tindex==0):
			fig = plt.figure()
			ax = fig.add_subplot(111)
			cont=ax.pcolor(np.fliplr(np.rot90(H,3)))
		else:
			cont.set_data(np.fliplr(np.rot90(H,3)))
			fig.canvas.draw()

		plt.show()
def main():

	infile='Torsk_polygon_2_kino_opendrift_01012012_to_30062012.nc'
	if os.path.exists(infile):
		cdf = Dataset(infile)
		xi,yi = createBins()
		calculateAreaAverages(xi,yi,cdf)

	else:
		print "Input file %s could not be opened"%(infile)

if __name__ == "__main__":
	main()

