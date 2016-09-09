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
o.io_import_file('results/Torsk_polygon_2_kino_opendrift_01012012_to_30092012.nc')
#o.plot(linecolor='z',vmin=20, vmax=0,filename='figures/Torsk_polygon_2_kino_opendrift_01012012_to_30062012.png')
o.plot(filename='figures/Torsk_polygon_2_kino_opendrift_01012012_to_30092012.png')
#o.animation(filename='figures/Torsk_polygon_2_kino_opendrift_01012012_to_30062012.mp4')
 
