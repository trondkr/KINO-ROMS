
import matplotlib.pyplot as plt
import ogr
import osr
from mpl_toolkits.basemap import Basemap

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

import numpy as np
import matplotlib.path as mpath
import matplotlib.patches as patches

def setupFigure():

	fig, ax = plt.subplots()
	patches = []
	mymap = Basemap(llcrnrlon=-18.0,
                      llcrnrlat=46.0,
                      urcrnrlon=25.5,
                      urcrnrlat=67.5,
                      resolution='i',projection='tmerc',lon_0=0,lat_0=50,area_thresh=250.)

	mymap.drawcoastlines()
	mymap.drawcountries()
	mymap.fillcontinents(color='grey')

	return fig,ax,patches,mymap

sf = "/Users/trondkr/Projects/Shapefiles/KINO_spawning_areas/Gadoid_spawning_areas/Torsk.shp"


targetSRS = osr.SpatialReference()
targetSRS.ImportFromEPSG(4326)
s = ogr.Open(sf)
s.GetLayerCount() #Check how many layers the file contains
layer = s.GetLayer(0) #Only one layer, extract this one
layer.GetFeatureCount() #Check how many features the layer contains

fig,ax,patches,mymap = setupFigure()
mypatches=[]
lon=[];lat=[]
for indexLayer in xrange(3):
	feature = layer.GetFeature(indexLayer) #The 4th feature contains the important spawning grounds
	#Find out if the feature is a point, polygon, multipolygon etc...
	geometry = feature.GetGeometryRef()
	numpolygons = geometry.GetGeometryCount() #The number of polygons
	print "Number of polygons %s in feature %s"%(numpolygons,indexLayer)
	
	# Create lists to store values for polygons
	codes = []; all_x = []; all_y = []
 	
	for poly in range(numpolygons):
		polygon_i = geometry.GetGeometryRef(poly) #Get the geometry contained within a specific polygon
		numpoints = polygon_i.GetPointCount()
		for point in range(numpoints):
			x, y, z = polygon_i.GetPoint(point)
			lon.append(x)
			lat.append(y)
	X,Y=mymap(lon,lat)
	mymap.plot(lon,lat)

plt.show()