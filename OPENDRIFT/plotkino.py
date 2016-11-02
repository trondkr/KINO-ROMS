#!/usr/bin/env python

from datetime import datetime, timedelta
import numpy as np

from opendrift.readers import reader_basemap_landmask
from opendrift.readers import reader_ROMS_native
from opendrift.models.oceandrift import OceanDrift
from kino.pelagicplankton import PelagicPlanktonDrift
from pprint import pprint
from netCDF4 import Dataset, datetime, date2num,num2date
from scipy.ndimage.filters import gaussian_filter
import ogr
import osr
import matplotlib
import os

o = PelagicPlanktonDrift(loglevel=0)  # Set loglevel to 0 for debug information

#######################
# Preparing readers
#######################
species=['Torsk_28102016_wgs84','Hyse_13102016_wgs84','Lyr_28102016_wgs84','Oyepaal_13102016_wgs84','Sei_13102016_wgs84','Whiting_13102016_wgs84'] 
base='results'
baseout='figures'
hexagon=False
timespan='15022012_to_15052012'

for speciesIndex,specie in enumerate(species):
		
	shapefile='/Users/trondkr/Projects/KINO/shapefile_spawning_areas/'+str(specie)+'.shp'
	if hexagon:
   		shapefile='/work/shared/imr/KINO/OPENDRIFT/shapefile_spawning_areas/'+str(specie)+'.shp'

	print "=> Using shapefile %s"%(shapefile)
	s = ogr.Open(shapefile)
	for layer in s:
		polygons=[x+1 for x in xrange(layer.GetFeatureCount()-1)]
			
		for polygonIndex,polygon in enumerate(polygons):
		
			feature = layer.GetFeature(polygonIndex)
			geom = feature.GetGeometryRef()
			points = geom.GetGeometryCount()
			ring = geom.GetGeometryRef(0)
	
			if ring.GetPointCount() > 3:
	
				filename=base+'/'+str(specie)+'_polygon_'+str(polygon)+'_kino_opendrift_'+str(timespan)+'.nc'
				plotfilename=baseout+'/'+str(specie)+'_polygon_'+str(polygon)+'_kino_opendrift_'+str(timespan)+'.png'
				plotfilenameColor=baseout+'/'+str(specie)+'_polygon_'+str(polygon)+'_kino_opendrift_'+str(timespan)+'_color.png'
				plotfilenameAnime=baseout+'/'+str(specie)+'_polygon_'+str(polygon)+'_kino_opendrift_'+str(timespan)+'.mp4'
				
				print "=> Opening input file: %s"%(os.path.basename(filename))
	
				if os.path.exists(filename):
					o.io_import_file(filename)
	
					#o.plot_vertical_distribution()
					#o.plot(linecolor='z',lvmin=-35, lvmax=0,filename=plotfilenameColor)
					o.plot(filename=plotfilename)
					#o.animation(filename=plotfilenameAnime)
			 
