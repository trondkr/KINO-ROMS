#!/usr/bin/env python

from datetime import datetime, timedelta
import numpy as np

from opendrift.readers import reader_basemap_landmask
from opendrift.readers import reader_ROMS_native
from kino.pelagicplankton import PelagicPlanktonDrift
from opendrift.readers import reader_netCDF_CF_generic
import logging
import gdal
import os
from netCDF4 import Dataset
from numpy.random import RandomState
import matplotlib.pyplot as plt
try:
    import ogr
    import osr
except Exception as e:
    print e
    raise ValueError('OGR library is needed to read shapefiles.')

def setupSeed(hoursBetweenTimestepInROMSFiles,startTime,endTime,startSpawningTime,endSpawningTime,releaseParticles):
    ##################################################
    # Create seed variation as function of day
    ##################################################

    # Make datetime array from start to end at 3 hour interval
    #interval = timedelta(hours=hoursBetweenTimestepInROMSFiles)
    difference=endTime-startTime
    hoursOfSimulation=divmod(difference.total_seconds(), 3600)
     
    difference=endSpawningTime-startSpawningTime
    hoursOfSpawning=divmod(difference.total_seconds(), 3600)
     
    #startSimulationJD=startTime.timetuple().tm_yday
    #endSimulationJD=endTime.timetuple().tm_yday
    timeStepsSimulation=int(int(hoursOfSimulation[0])/hoursBetweenTimestepInROMSFiles)
	
    #startSpawningJD=startSpawningTime.timetuple().tm_yday
    #endSpawningJD=endSpawningTime.timetuple().tm_yday
    #timeStepsSpawning=int(int(hoursOfSpawning[0])/hoursBetweenTimestepInROMSFiles)
	
    print "\nKINO TIME EVOLUTION:"
    print "=>SIMULATION: Drift simulation will run for %s simulation hours" %(timeStepsSimulation)
    print "=>SPAWNING: Simulated spawning will run for %s simulation hours\n initiated on %s and ending on %s"%(timeStepsSimulation,startSpawningTime,endSpawningTime)

    interval = timedelta(hours=24)
    hoursPerSpawning=divmod(interval.total_seconds(), 3600) #hours per spawning event
    timeStepsSpawning=int(int(hoursOfSpawning[0])/int(hoursPerSpawning[0])) #number of spawning timesteps
    spawningTimes = [startSpawningTime + interval*n for n in range(timeStepsSpawning)] #times of spawning

    # Normal distribution around 0.5
    mu, sigma = 0.5, 0.1 # mean and standard deviation

    prng = RandomState()
    scale = prng.randint(1, 5, size=1)

    prng = RandomState()
    s = prng.normal(mu, sigma, len(spawningTimes))
    num=(s*releaseParticles).astype(int)
    num=np.sort(num) #sort particles in increasing order
    num=np.concatenate((num[len(num)%2::2],num[::-2]),axis=0) #release the highest number of particles at the midpoint of the spawning period

    print "SPAWNING: Simulated spawning will release %s eggs"%(np.sum(num))

    return num, spawningTimes


def createOutputFilenames(startTime,endTime,polygonIndex,specie,shapefile):
    startDate=''
    if startTime.day<10:
        startDate+='0%s'%(startTime.day)
    else:
        startDate+='%s'%(startTime.day)

    if startTime.month<10:
        startDate+='0%s'%(startTime.month)
    else:
        startDate+='%s'%(startTime.month)

    startDate+='%s'%(startTime.year)

    endDate=''
    if endTime.day<10:
        endDate+='0%s'%(endTime.day)
    else:
        endDate+='%s'%(endTime.day)

    if endTime.month<10:
        endDate+='0%s'%(endTime.month)
    else:
        endDate+='%s'%(endTime.month)

    endDate+='%s'%(endTime.year)
 
    # Special file naming for KINO. Each layer has name 'species.shp' and we want teh species name only.
    head,tail=os.path.split(shapefile)
    species=os.path.splitext(tail)
    outputFilename='results/%s_polygon_%s_kino_opendrift_%s_to_%s.nc'%(specie,polygonIndex,startDate,endDate)
    animationFilename='figures/%s_polygon_%s_kino_animation_%s_to_%s.mp4'%(specie,polygonIndex,startDate,endDate)
    plotFilename='figures/%s_polygon_%s_kino_plot_%s_to_%s.png'%(specie,polygonIndex,startDate,endDate)

    if not os.path.exists('figures'):
        os.makedirs('figures')
    if not os.path.exists('results'):
        os.makedirs('results')
    return outputFilename, animationFilename, plotFilename

   
def createAndRunSimulation(lowDepth,highDepth,endTime,layer,layerName,polygonIndex,shapefile,specie,outputFilename,animationFilename,plotFilename,releaseParticles,kinoDirectory,pattern_kino,svimDirectory,pattern_svim,hexagon):

    # Setup a new simulation
    o = PelagicPlanktonDrift(loglevel=0)  # Set loglevel to 0 for debug information

    #######################
    # Preparing readers
    #######################
    o.add_reader([reader_basemap])
       
    reader_kino = reader_ROMS_native.Reader(kinoDirectory+pattern_kino)
    reader_kino.interpolation = 'nearest' #linearND
    reader_svim = reader_ROMS_native.Reader(svimDirectory+pattern_svim)
    reader_svim.interpolation = 'nearest' #linearND
    if hexagon:
        o.add_reader([reader_kino,reader_svim])
       # o.add_reader([reader_kino])
    else:
        o.add_reader([reader_kino])

    num, spawningTimes = setupSeed(hoursBetweenTimestepInROMSFiles,startTime,endTime,startSpawningTime,endSpawningTime,releaseParticles)
 
    #######################
    #Adjusting configuration
    #######################
    o.config['processes']['turbulentmixing'] = True
    o.config['turbulentmixing']['diffusivitymodel'] = 'windspeed_Sundby1983'
    o.config['turbulentmixing']['timestep'] = 900 # seconds
    o.config['turbulentmixing']['verticalresolution'] = 1 # default is 1 meter, but since we have longer timestep we justify it
    o.config['processes']['verticaladvection'] = True
    o.config['turbulentmixing']['TSprofiles'] = False
    o.config['drift']['scheme'] = 'euler'

    #######################
    # IBM configuration   
    #######################
    o.config['biology']['constantIngestion'] = 0.3
    o.config['biology']['activeMetabOn'] = 1
    o.config['biology']['cod'] = True
    o.config['biology']['haddock'] = False
    o.config['biology']['attenuationCoefficient']=0.18
    o.config['biology']['fractionOfTimestepSwimming']=0.05 # Pause-swim behavior
    o.config['biology']['lowerStomachLim']=0.3 #Min. stomach fullness needed to actively swim down

    #######################
    # Seed particles
    #######################
    prng = RandomState()
    for i, nums in enumerate(num):

        if nums <= 0:
            continue
        print "Running i=%s num=%s for species=%s and polygon=%s"%(i,nums,layerName,polygonIndex)
        o.seed_from_shapefile(shapefile, nums, layername=specie,featurenum=[polygonIndex], z=prng.randint(lowDepth, highDepth, nums), time=spawningTimes[i])

    print "Elements scheduled for %s : %s"%(specie,o.elements_scheduled)
    #reader_basemap.plot() 

    #########################
    # Run the model
    #########################
    o.run(end_time=endTime, time_step=timedelta(hours=2),
          outfile=outputFilename)
          #export_variables=['lon', 'lat', 'z','temp','length','weight','survival'])

#########################
# SETUP FOR KINO PROJECT
#########################

hexagon=True
startTime=datetime(2012,2,15,12,3,50)
endTime=datetime(2012,5,15,12,3,50)
startSpawningTime=startTime
endSpawningTime=datetime(2012,4,15,12,3,50)
releaseParticles=50 # Per timestep multiplied by gaussian bell (so maximum is releaseParticles and minimum is close to zero)
lowDepth, highDepth = -20, 0 # in negative meters

hoursBetweenTimestepInROMSFiles=3
species=['Torsk_28102016_wgs84','Hyse_13102016_wgs84','Lyr_28102016_wgs84','Oyepaal_13102016_wgs84','Sei_13102016_wgs84','Whiting_13102016_wgs84'] 
species=['Hyse_03112016_wgs84']
    
if not hexagon: 
    kinoDirectory='/Users/trondkr/Projects/KINO/RESULTS/'
    svimDirectory='/Users/trondkr/Projects/KINO/RESULTS/'

    startTime=datetime(2010,8,3,19,3,50)
    endTime=datetime(2010,8,3,21,3,50)
    startSpawningTime=datetime(2010,8,3,19,3,50)
    endSpawningTime=datetime(2010,8,4,19,3,50)

if hexagon:
    kinoDirectory='/work/users/trondk/KINO/FORWARD/Run/RESULTS/'+str(startTime.year)+'/'
    svimDirectory='/work/shared/imr/SVIM/'+str(startTime.year)+'/'

if not hexagon:
    pattern_kino='kino_1600m_*[\U22859-\U22861]*.nc'
    pattern_svim='kino_1600m_*[\U22859-\U22861]*.nc'
else:
    # Year 2011 => 23011-23375
    #pattern='kino_1600m_*[\U23011-\U23375]*.nc' 
    pattern_kino='kino_1600m_*.nc' 
    pattern_svim='ocean_avg_*.nc' 

# Landmask (Basemap)
reader_basemap = reader_basemap_landmask.Reader(
                        llcrnrlon=-8.0, llcrnrlat=50.5,
                        urcrnrlon=30.0, urcrnrlat=75.0,
                        resolution='i', projection='merc')

# Loop over all species
for specie in species:
    if not hexagon:
        shapefile='/Users/trondkr/Projects/KINO/shapefile_spawning_areas/'+str(specie)+'.shp'
    if hexagon:
        shapefile='/work/shared/imr/KINO/OPENDRIFT/shapefile_spawning_areas/'+str(specie)+'.shp'
   
    print "=> Using shapefile %s"%(shapefile)
    s = ogr.Open(shapefile)

    for layer in s:
        polygons=[x+1 for x in xrange(layer.GetFeatureCount()-1)]
        
        for polygonIndex in polygons:
            
            feature = layer.GetFeature(polygonIndex-1)
           
            geom = feature.GetGeometryRef()
            points = geom.GetGeometryCount()
            ring = geom.GetGeometryRef(0)
            if ring.GetPointCount() > 3:
                outputFilename, animationFilename, plotFilename = createOutputFilenames(startTime,endTime,polygonIndex,specie,shapefile)
              
                print "Result files will be stored as:\nnetCDF=> %s\nmp4=> %s"%(outputFilename,animationFilename)

                createAndRunSimulation(lowDepth,highDepth,endTime,
                    layer,specie,polygonIndex,shapefile,
                    specie,outputFilename,
                    animationFilename,plotFilename,releaseParticles,kinoDirectory,
                    pattern_kino,svimDirectory,pattern_svim,hexagon)

