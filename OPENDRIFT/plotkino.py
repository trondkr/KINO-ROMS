#!/usr/bin/env python

from datetime import datetime, timedelta
import numpy as np

from opendrift.readers import reader_basemap_landmask
from opendrift.readers import reader_ROMS_native
from opendrift.models.oceandrift import OceanDrift
from kino.pelagicplankton import PelagicPlanktonDrift

o = PelagicPlanktonDrift(loglevel=0)  # Set loglevel to 0 for debug information

#######################
# Preparing readers
#######################


for polygonIndex in [1,2,3]:
	filename='results/Torsk_polygon_'+str(polygonIndex)+'_kino_opendrift_15022012_to_30052012.nc'
	plotfilename='results/Torsk_polygon_'+str(polygonIndex)+'_kino_opendrift_15022012_to_30052012.png'
	plotfilenameColor='results/Torsk_polygon_'+str(polygonIndex)+'_kino_opendrift_15022012_to_30052012_color.png'
	plotfilenameAnime='results/Torsk_polygon_'+str(polygonIndex)+'_kino_opendrift_15022012_to_30052012_color.mp4'
	
	print filename
	o.io_import_file(filename)

	#o.plot_vertical_distribution()
	o.plot(linecolor='z',lvmin=-25, lvmax=0,filename=plotfilenameColor)
	o.plot(filename=plotfilename)
	o.animation(filename=plotfilenameAnime)
	 
