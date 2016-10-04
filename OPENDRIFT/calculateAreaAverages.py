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
from scipy.ndimage.filters import gaussian_filter

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
	ymin=50.0; ymax=66.0
	requiredResolution = 10 # km between each binned box

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

def calculateAreaAverages(xi,yi,cdf,first):

	print 'func: calculateAreaAverages() => Calculating averages within bins'
	print '=> binned domain (%2.1f,%2.1f) to (%2.1f,%2.1f)'%(np.min(xi),np.min(yi),np.max(xi),np.max(yi))

	timesteps = cdf.variables['time'][:]
 	timeunits = cdf.variables["time"].units

	print '=> found %s timesteps in input file'%(len(timesteps))

	for tindex, t in enumerate(timesteps): 

 		currentDate = num2date(t, units=timeunits, calendar="gregorian")
		Xpos = cdf.variables['lon'][:,tindex]
		Ypos = cdf.variables['lat'][:,tindex]
			
		H, xedges, yedges = np.histogram2d(Xpos, Ypos, bins=(xi, yi), normed=False)

		if (tindex==0 and first is True):
			monthlyFrequency=np.zeros((12,np.shape(H)[0],np.shape(H)[1]), dtype=float32)
			print np.shape(monthlyFrequency)
			
	#	if currentDate.month==2:
		print "=> Adding data to month: %s (%s)"%(currentDate.month,currentDate)
		monthlyFrequency[currentDate.month,:,:]=monthlyFrequency[currentDate.month,:,:] + H

	# Create log values and levels for frequencyplot
	monthlyFrequency=ma.log(monthlyFrequency)
	levels = np.arange(monthlyFrequency.min(),monthlyFrequency.max(),(monthlyFrequency.max()- monthlyFrequency.min())/10)
		
	sigma = 0.2 # this depends on how noisy your data is, play with it!

	filtereddata = gaussian_filter(monthlyFrequency, sigma)

	# Create one plot per month
	for month in [1,2,3,4]:
	
		plt.clf()
		plt.figure(figsize=(10,10), frameon=False)

		mymap = Basemap(llcrnrlon=-3.0,
	                  llcrnrlat=53.0,
	                  urcrnrlon=13.5,
	                  urcrnrlat=63.0,
	                  resolution='i',projection='tmerc',lon_0=5,lat_0=10,area_thresh=50.)

		xii,yii=np.meshgrid(xi[:-1],yi[:-1])
		x, y = mymap(xii,yii)
		
		CS1 = mymap.contourf(x,y,np.fliplr(np.rot90(np.squeeze(filtereddata[month,:,:]),3)),levels,cmap=cm.get_cmap('Spectral_r',len(levels)-1), extend='both',alpha=1.0)
		plt.colorbar(CS1,orientation='vertical',extend='both', shrink=0.5)

		mymap.drawcoastlines()
		mymap.fillcontinents(color='grey',zorder=2)
		mymap.drawcountries()
		mymap.drawmapboundary()
		plt.title('Month %s'%(month))
		plotfile='/Users/trondkr/Projects/KINO/opendrift/frequencyFigures/frequency_'+str(month)+'.png'
		print "=> Creating plot %s"%(plotfile)
		#plt.show()
		plt.savefig(plotfile,dpi=300)

def main():

	first=True
	infile='results/Torsk_polygon_1_kino_opendrift_15022012_to_30052012.nc'

	xi,yi = createBins()

	if os.path.exists(infile):
		cdf = Dataset(infile)
		first = calculateAreaAverages(xi,yi,cdf,first)

	else:
		print "Input file %s could not be opened"%(infile)

if __name__ == "__main__":
	main()

