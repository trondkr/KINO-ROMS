# coding=utf-8

import os, sys
import numpy as np
import glob
import string
from matplotlib.pyplot import cm 
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from pylab import *
import datetime
from pprint import pprint
from netCDF4 import Dataset, datetime, date2num,num2date
from scipy.ndimage.filters import gaussian_filter
import ogr
import osr
import matplotlib
matplotlib.use('Agg')

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

def createBins(requiredResolution):

	print 'func: createBins() => Creating bins for averaging'
	xmin=-4.0; xmax=13.0
	ymin=50.0; ymax=66.0
	
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

	print '=> created binned array of domain of size (%s,%s) with resolution %s'%(ngridx,ngridy,requiredResolution)

	return xi,yi

def calculateAreaAverages(xi,yi,cdf,first,survivalDefinedDistribution):

	print 'func: calculateAreaAverages() => Calculating averages within bins'
	print '=> binned domain (%2.1f,%2.1f) to (%2.1f,%2.1f)'%(np.min(xi),np.min(yi),np.max(xi),np.max(yi))

	timesteps = cdf.variables['time'][:]
 	timeunits = cdf.variables["time"].units
	
	print '=> found %s timesteps in input file'%(len(timesteps))
	newMonth=-9

	for tindex, t in enumerate(timesteps): 

 		currentDate = num2date(t, units=timeunits, calendar="gregorian")
		Xpos = cdf.variables['lon'][:,tindex]
		Ypos = cdf.variables['lat'][:,tindex]

		if survivalDefinedDistribution:
			survival=cdf.variables['survival'][:,tindex]
			H, xedges, yedges = np.histogram2d(Xpos, Ypos, weights=survival, bins=(xi, yi), normed=False)
		else:
			H, xedges, yedges = np.histogram2d(Xpos, Ypos, bins=(xi, yi), normed=False)

		if (tindex==0 and first is True):
			monthlyFrequency=np.zeros((12,np.shape(H)[0],np.shape(H)[1]), dtype=float32)
			
		if currentDate.month != newMonth:
			print "=> Adding data to month: %s (startdate: %s)"%(currentDate.month,currentDate)
			newMonth=currentDate.month
		monthlyFrequency[currentDate.month,:,:]=monthlyFrequency[currentDate.month,:,:] + H
		
	# Create log values and levels for frequencyplot
	monthlyFrequency=ma.log(monthlyFrequency)
	levels = np.arange(monthlyFrequency.min(),monthlyFrequency.max(),(monthlyFrequency.max()- monthlyFrequency.min())/10)
		
	sigma = 0.2 # this depends on how noisy your data is, play with it!
	first=False

	return gaussian_filter(monthlyFrequency, sigma), first

def plotDistribution(shapefile,speciesData,month,specie,baseout,xii,yii,survivalDefinedDistribution):
	print "Plotting the distributions for month: %s"%(month)
	plt.clf()
	plt.figure(figsize=(10,10), frameon=False)
        ax = plt.subplot(111)

	mymap = Basemap(llcrnrlon=-3.0,
	                  llcrnrlat=53.0,
	                  urcrnrlon=13.5,
	                  urcrnrlat=63.0,
	                  resolution='i',projection='tmerc',lon_0=5,lat_0=10,area_thresh=50.)

	
	x, y = mymap(xii,yii)
		
	levels=np.arange(np.min(speciesData),np.max(speciesData),0.5)
                              
	CS1 = mymap.contourf(x,y,np.fliplr(np.rot90(speciesData,3)),levels,cmap=cm.get_cmap('Spectral_r',len(levels)-1), extend='both',alpha=1.0)
	plt.colorbar(CS1,orientation='vertical',extend='both', shrink=0.5)

	mymap.drawcoastlines()
	mymap.fillcontinents(color='grey',zorder=2)
	mymap.drawcountries()
	mymap.drawmapboundary()

	plt.title('Species: %s month: %s'%(specie,month))
	if survivalDefinedDistribution:
		plotfile=baseout+'/'+str(specie)+'_distribution_'+str(month)+'_survivalDefinedDistribution.png'
	else:
		plotfile=baseout+'/'+str(specie)+'_distribution_'+str(month)+'.png'
	print "=> Creating plot %s"%(plotfile)
	plt.savefig(plotfile,dpi=300)

        print "Adding polygons to plot"

        mypatches=createPathsForPolygons(shapefile,mymap)
        p = PatchCollection(mypatches,alpha=1.0,facecolor='none',lw=1.0,edgecolor='purple',zorder=2)
        ax.add_collection(p)
        plt.title('Species: %s month: %s'%(specie,month))

        if survivalDefinedDistribution:
                plotfile=baseout+'/'+str(specie)+'_distribution_'+str(month)+'_spawningground__survivalDefinedDistribution.png'
        else:
                plotfile=baseout+'/'+str(specie)+'_distribution_'+str(month)+'_spawningground.png'
                print "=> Creating plot %s"%(plotfile)
                 
        plt.savefig(plotfile,dpi=300)
                                                                

def getPathForPolygon(ring,mymap):
	codes=[]
	x = [ring.GetX(j) for j in range(ring.GetPointCount())]
	y = [ring.GetY(j) for j in range(ring.GetPointCount())]
        codes += [mpath.Path.MOVETO] + (len(x)-1)*[mpath.Path.LINETO]
    
	pathX,pathY=mymap(x,y)
        mymappath = mpath.Path(np.column_stack((pathX,pathY)), codes)

	return mymappath
   
def createPathsForPolygons(shapefile,mymap):

	mypatches=[]
	s = ogr.Open(shapefile)
        for layer in s:

                polygons=[x+1 for x in xrange(layer.GetFeatureCount()-1)]
                for polygonIndex,polygon in enumerate(polygons):
                        feature = layer.GetFeature(polygonIndex)
                        geom = feature.GetGeometryRef()
                        points = geom.GetGeometryCount()
                        ring = geom.GetGeometryRef(0)
                        
			if ring.GetPointCount() > 3:
				polygonPath = getPathForPolygon(ring,mymap)
                                path_patch = mpatches.PathPatch(polygonPath, lw=2, edgecolor="purple",facecolor='none')
                                
                                mypatches.append(path_patch)
        return mypatches

def main():

	# EDIT --------------------------------------
	# Which species to calculate for
	species=['Hyse_03112016_wgs84']
	#species=['Lyr_28102016_wgs84','Hyse_13102016_wgs84']
	#species=['Torsk_28102016_wgs84','Hyse_13102016_wgs84','Lyr_28102016_wgs84','Oyepaal_13102016_wgs84','Sei_13102016_wgs84','Whiting_13102016_wgs84'] 

	# The timespan part of the filename
	timespan='15022012_to_15052012'
	#timespan='15022012_to_15042012'

	# Results and storage folders
	base='results'
	baseout='distributionFigures'

	# What months you want to calculate distributions for 
	months=[2,3,4,5]
      
	# The resolution of the output grid in kilometers
	requiredResolution = 10 # km between each binned box

	# Modify distributions using survival rates
	survivalDefinedDistribution=True

	# END EDIT ----------------------------------

	# Create the grid you want to calculate frequency on
	xi,yi = createBins(requiredResolution)
	monthsInYear=12
	xii,yii=np.meshgrid(xi[:-1],yi[:-1])
	firstRead=True
	hexagon=False
	maxNumberOfPolygons=14

	for speciesIndex,specie in enumerate(species):
		
		shapefile='/Users/trondkr/Projects/KINO/shapefile_spawning_areas/'+str(specie)+'.shp'
		if hexagon:
   			shapefile='/work/shared/imr/KINO/OPENDRIFT/shapefile_spawning_areas/'+str(specie)+'.shp'

                print "=> Using shapefile %s"%(shapefile)
                s = ogr.Open(shapefile)
                for layer in s:
                        polygons=[x+1 for x in xrange(layer.GetFeatureCount()-1)]
                if firstRead:
                        allData=np.zeros((len(species),maxNumberOfPolygons,monthsInYear,len(xi)-1,len(yi)-1))
                        print "=> Created final array for all data of size :",np.shape(allData)
                        firstRead=False

		for polygonIndex,polygon in enumerate(polygons):
			first=True
			
			feature = layer.GetFeature(polygonIndex)
			geom = feature.GetGeometryRef()
			points = geom.GetGeometryCount()
			ring = geom.GetGeometryRef(0)
			if ring.GetPointCount() > 3:
				infile=base+'/'+str(specie)+'_polygon_'+str(polygon)+'_kino_opendrift_'+str(timespan)+'.nc'
				print "=> Opening input file: %s"%(os.path.basename(infile))

				if os.path.exists(infile):
					cdf = Dataset(infile)
					filteredData, first = calculateAreaAverages(xi,yi,cdf,first,survivalDefinedDistribution)
					print np.shape(filteredData), polygonIndex,speciesIndex,np.shape(allData)
					allData[speciesIndex,polygonIndex,:,:,:]=filteredData
				else:
					print "==>> Input file %s could not be opened"%(infile)

	for speciesIndex,specie in enumerate(species):

		shapefile='/Users/trondkr/Projects/KINO/shapefile_spawning_areas/'+str(specie)+'.shp'
		if hexagon:
                        shapefile='/work/shared/imr/KINO/OPENDRIFT/shapefile_spawning_areas/'+str(specie)+'.shp'
   		print "Creating figures for species: %s"%(specie)
	
		for month in months:
                        # Calculate the cumulative distribution for each month and species
                        first=True
                        for polygonIndex,polygon in enumerate([x+1 for x in xrange(len(polygons))]):
                                if first:
                                        speciesData=np.zeros((len(xi)-1,len(yi)-1))
                                        first=False
                                        print "==> Created array of data for month: ",month," with size: ",np.shape(speciesData)

                                speciesData=speciesData + np.squeeze(allData[speciesIndex,polygonIndex,month,:,:])
			levels=np.arange(np.min(speciesData),np.max(speciesData),0.5)
			if len(levels)>2:
				plotDistribution(shapefile,speciesData,month,specie,baseout,xii,yii,survivalDefinedDistribution)

if __name__ == "__main__":
	main()

