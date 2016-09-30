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
import matplotlib.pyplot as plt
try:
    import ogr
    import osr
except Exception as e:
    print e
    raise ValueError('OGR library is needed to read shapefiles.')

def setupSeed(hoursBetweenTimestepInROMSFiles,startTime,endTime,startSpawningTime,endSpawningTime):
    ##################################################
    # Create seed variation as function of day
    ##################################################

    # Make datetime array from start to end at 3 hour interval
    interval = timedelta(hours=hoursBetweenTimestepInROMSFiles)
    difference=endTime-startTime
    hoursOfSimulation=divmod(difference.total_seconds(), 3600)
     
    difference=endSpawningTime-startSpawningTime
    hoursOfSpawning=divmod(difference.total_seconds(), 3600)
     
    startSimulationJD=startTime.timetuple().tm_yday
    endSimulationJD=endTime.timetuple().tm_yday
    timeStepsSimulation=int(int(hoursOfSimulation[0])/hoursBetweenTimestepInROMSFiles)

    startSpawningJD=startSpawningTime.timetuple().tm_yday
    endSpawningJD=endSpawningTime.timetuple().tm_yday
    timeStepsSpawning=int(int(hoursOfSpawning[0])/hoursBetweenTimestepInROMSFiles)


    print "\nKINO TIME EVOLUTION:"
    print "=>SIMULATION: Drift simulation will run for %s simulation hours" %(timeStepsSimulation)
    print "=>SPAWNING: Simulated spawning will run for %s simulation hours\n initiated on %s and ending on %s"%(timeStepsSpawning,startSpawningTime,endSpawningTime)

    interval = timedelta(hours=24)

    spawningTimes = [startSpawningTime + interval*n for n in range(timeStepsSpawning)]


    # Normal distribution around 0.5
    mu, sigma = 0.5, 0.1 # mean and standard deviation
    s = np.random.normal(mu, sigma, len(spawningTimes))
    num=(s*scaleFactor*10).astype(int)
 
    print "SPAWNING: Simulated spawning will release %s eggs"%(np.sum(num))

 #   for day,seed in zip(spawningTimes,num):
 #       print "=> day: %s seed: %s"%(day,seed)

    #count, bins, ignored = plt.hist(num, 30, normed=True)
    #plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) *
    #               np.exp( - (bins - mu)**2 / (2 * sigma**2) ),
    #         linewidth=2, color='r')
    #plt.show()

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

   
def createAndRunSimulation(endTime,layer,polygonIndex,shapefile,specie,outputFilename,animationFilename,plotFilename):

    # Setup a new simulation
    o = PelagicPlanktonDrift(loglevel=0)  # Set loglevel to 0 for debug information

    #######################
    # Preparing readers
    #######################
    o.add_reader([reader_basemap])
       
    reader_roms = reader_ROMS_native.Reader(romsDirectory+pattern)
    reader_roms.interpolation = 'nearest' #linearND
    o.add_reader(reader_roms)

    num, spawningTimes = setupSeed(hoursBetweenTimestepInROMSFiles,startTime,endTime,startSpawningTime,endSpawningTime)

    #######################
    #Adjusting configuration
    #######################
    o.config['processes']['turbulentmixing'] = True
    o.config['turbulentmixing']['diffusivitymodel'] = 'windspeed_Sundby1983'
    o.config['turbulentmixing']['timestep'] = 100 # seconds
    o.config['turbulentmixing']['verticalresolution'] = 2 # default is 1 meter, but since we have longer timestep we justify it
    o.config['processes']['verticaladvection'] = True
    o.config['turbulentmixing']['TSprofiles']=True

    #######################
    # IBM configuration   
    #######################
    o.config['biology']['constantIngestion'] = 0.3
    o.config['biology']['activeMetabOn'] = 1
    o.config['biology']['cod'] = True
    o.config['biology']['haddock'] = False
    o.config['biology']['attenuationCoefficient']=0.18
    
    #######################
    # Seed particles
    #######################
    for i, nums in enumerate(num):
        if nums <= 0:
            continue
        print "Running i=%s num=%s"%(i,nums)
        o.seed_from_shapefile(shapefile, nums, layername='Torsk',featurenum=[polygonIndex], z=-10, time=spawningTimes[i])

    print "Elements scheduled for %s : %s"%(specie,o.elements_scheduled)
    #reader_basemap.plot() 

    #########################
    # Run the model
    #########################
    o.run(end_time=endTime, time_step=timedelta(hours=3),
          outfile=outputFilename,
          export_variables=['lon', 'lat', 'z','temp','length','weight'])

    if not hexagon:
        o.plot(linecolor='z',filename=plotFilename)
        o.animation(filename=animationFilename)

#########################
# SETUP FOR KINO PROJECT
#########################

hexagon=True
startTime=datetime(2012,2,15,12,3,50)
endTime=datetime(2012,5,30,3,3,50)
startSpawningTime=datetime(2012,2,15,12,3,50)
endSpawningTime=datetime(2012,4,15,3,3,50)

scaleFactor=1 # if scaleFactor=1, total particles is 1000, scaleFactor=2, total particles = 2000
hoursBetweenTimestepInROMSFiles=3
species=['Torsk'] #['Sei','Oyepaal','Hyse','Torsk']

if not hexagon: 
    romsDirectory='/Users/trondkr/Projects/KINO/RESULTS/'
    startTime=datetime(2010,8,3,19,3,50)
    endTime=datetime(2010,8,5,17,3,50)
    startSpawningTime=datetime(2010,8,3,19,3,50)
    endSpawningTime=datetime(2010,8,4,19,3,50)

if hexagon:
    romsDirectory='/work/users/trondk/KINO/FORWARD/Run/RESULTS/2012/'

if not hexagon:
    pattern='kino_1600m_*[\U22859-\U22861]*.nc'
else:
    # Year 2011 => 23011-23375
    pattern='kino_1600m_*[\U23011-\U23375]*.nc' 
    pattern='kino_1600m_*.nc' 

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
    print "Using shapefile %s"%(shapefile)
    s = ogr.Open(shapefile)

    for layer in s:
        
        for polygonIndex in [1,2,3]:
            outputFilename, animationFilename, plotFilename = createOutputFilenames(startTime,endTime,polygonIndex,specie,shapefile)

            print "Result files will be stored as:\nnetCDF=> %s\nmp4=> %s"%(outputFilename,animationFilename)

            createAndRunSimulation(endTime,layer,polygonIndex,shapefile,specie,outputFilename,animationFilename,plotFilename)

