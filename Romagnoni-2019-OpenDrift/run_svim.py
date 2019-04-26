#!/usr/bin/env python
from __future__ import print_function

print(1)
import matplotlib
matplotlib.use('TkAgg')
print(2)
import time
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
print(3)
from opendrift.readers import reader_basemap_landmask
from opendrift.readers import reader_ROMS_native
from kino.pelagicplankton import PelagicPlanktonDrift
from opendrift.readers import reader_netCDF_CF_generic
import logging
import gdal
import os
#from netCDF4 import Dataset, datetime, date2num,num2date
print(4)
from numpy.random import RandomState
import matplotlib.pyplot as plt
try:
    import ogr
    import osr
except Exception as e:
    print (e)
    raise ValueError('OGR library is needed to read shapefiles.')
print(5)
def setupSeed(hoursBetweenTimestepInROMSFiles,startTime,endTime,startSpawningTime,endSpawningTime,releaseParticles):
    ##################################################
    # Create seed variation as function of day
    ##################################################

    # Make datetime array from start to end at 3 hour interval
    difference=endTime-startTime
    hoursOfSimulation=divmod(difference.total_seconds(), 3600)
    difference=endSpawningTime-startSpawningTime
    hoursOfSpawning=divmod(difference.total_seconds(), 3600)
    timeStepsSimulation=int(int(hoursOfSimulation[0])/hoursBetweenTimestepInROMSFiles)
		
    print ("\nsvim TIME EVOLUTION:")
    print ("=>SIMULATION: Drift simulation will run for %s simulation hours" %(timeStepsSimulation))
    print ("=>SPAWNING: Simulated spawning will run for %s simulation hours\n initiated on %s and ending on %s"%(timeStepsSimulation,startSpawningTime,endSpawningTime))

    interval = timedelta(hours=24)
    hoursPerSpawning=divmod(interval.total_seconds(), 3600) #hours per spawning event
    timeStepsSpawning=int(int(hoursOfSpawning[0])/int(hoursPerSpawning[0])) #number of spawning timesteps
    spawningTimes = [startSpawningTime + interval*n for n in range(timeStepsSpawning)] #times of spawning

    # Define number of particles released per spawning day, summing to ~releaseParticles and following a gaussian curve
    mu, sigma = 1, 0.25 # mean and standard deviation of the gaussian curve 
    prng = RandomState(1) # random number generator (specify number to ensure the same sequence each time)
    s = prng.normal(mu, sigma, timeStepsSpawning) # random distribution
    num=(s*releaseParticles/timeStepsSpawning).astype(int) # number of particles released per spawning event as releaseParticles/timeStepsSpawning, weighted by random distribution
    num=np.sort(num) #sort particles in increasing order 
    num=np.concatenate((num[len(num)%2::2],num[::-2]),axis=0) #release the highest number of particles at the midpoint of the spawning period
	
    print ("SPAWNING: Simulated spawning will release %s eggs"%(np.sum(num)))

    return num, spawningTimes

print(6)

def createOutputFilenames(startTime,endTime,verticalBehavior,spawning_ground):
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
 
    # File naming
    if verticalBehavior:
        outputFilename='results_stock_recruitment/opendrift_%s_%s_to_%s_vertical.nc'%(spawning_ground,startDate,endDate)
        animationFilename='figures/animation_%s_%s_to_%s_vertical.mp4'%(spawning_ground,startDate,endDate)
        plotFilename='figures/plot_%s_%s_to_%s_vertical.png'%(spawning_ground,startDate,endDate)
    else:
        outputFilename='results_stock_recruitment/opendrift_%s_%s_to_%s_novertical.nc'%(spawning_ground,startDate,endDate)
        animationFilename='figures/animation_%s_%s_to_%s_novertical.mp4'%(spawning_ground,startDate,endDate)
        plotFilename='figures/plot_%s_%s_to_%s_novertical.png'%(spawning_ground,startDate,endDate)
    if not os.path.exists('figures'):
        os.makedirs('figures')
    if not os.path.exists('results'):
        os.makedirs('results')
    return outputFilename, animationFilename, plotFilename

print(7)
   
def createAndRunSimulation(lowDepth,highDepth,endTime,shapefile,outputFilename,animationFilename,plotFilename,releaseParticles,pattern_svim,verticalBehavior,spawning_ground):

    # Setup a new simulation
    o = PelagicPlanktonDrift(loglevel=0)  # Set loglevel to 0 for debug information
    #o.max_speed = 10
    #######################
    # Preparing readers
    #######################
    reader_basemap = reader_basemap_landmask.Reader(
                       llcrnrlon=-7, llcrnrlat=50,
                       urcrnrlon=15, urcrnrlat=65,
                       resolution='i', projection='merc')
                       
    o.add_reader([reader_basemap]) #Note: Include because of issue with linearNDfast
    o.set_config('general:basemap_resolution', 'i')
    reader_svim = reader_ROMS_native.Reader(pattern_svim)#SVIM reader used to cover area outside svim reader
    o.add_reader([reader_svim]) #FORCE loaded for wind information
    

    num, spawningTimes = setupSeed(hoursBetweenTimestepInROMSFiles,startTime,endTime,startSpawningTime,endSpawningTime,releaseParticles)
 
    #######################
    #Adjusting configuration
    #######################
    if verticalBehavior:
        o.set_config('processes:turbulentmixing', True)
    else:
        o.set_config('processes:turbulentmixing',  False)
    o.set_config('turbulentmixing:diffusivitymodel','windspeed_Sundby1983')
    o.set_config('turbulentmixing:timestep', 4) # seconds
    o.set_config('turbulentmixing:verticalresolution', 2) # default is 1 meter, but since we have longer timestep we justify it
    if verticalBehavior:
        o.set_config('processes:verticaladvection', False)
    else:
        o.set_config('processes:verticaladvection', False)
    o.set_config('turbulentmixing:TSprofiles', False)
    #o.set_config('turbulentmixing:max_iterations', 400) #200 used in ms version
    o.set_config('drift:scheme', 'euler')
    o.set_config('general:coastline_action', 'previous') #Prevent stranding, jump back to previous position
    

    #######################
    # IBM configuration   
    #######################
    o.set_config('biology:constantIngestion', 0.75)
    o.set_config('biology:activemetabOn', 1)
    o.set_config('biology:cod', True)
    o.set_config('biology:haddock', False)
    o.set_config('biology:attenuationCoefficient',0.18)
    if verticalBehavior:
        o.set_config('biology:fractionOfTimestepSwimming',0.15) # Pause-swim behavior
    else:
        o.set_config('biology:fractionOfTimestepSwimming',0.00) # Pause-swim behavior
    o.set_config('biology:lowerStomachLim',0.3) #Min. stomach fullness needed to actively swim down
    
 
    #######################
    # Seed particles
    #######################
    #Fixed distribution in depth:
    def eq_div(N, i):
        return [] if i <= 0 else [N / i + 1] * (N % i) + [N / i] * (i - N % i)
    z_levels=range(lowDepth,highDepth+1,10) #levels of depth distribution
    for i, nums in enumerate(num):

        if nums <= 0:
            continue
        z_dist=eq_div(nums,len(z_levels)) #number of particles per level (approx. equal)
        print ("Running i=%s num=%s for spawning ground=%s"%(i,nums,spawning_ground))
        print ("Depths ",np.repeat(z_levels,z_dist))
        o.seed_from_shapefile(shapefile, nums, layername=None,featurenum=[1], z=np.repeat(z_levels,z_dist), time=spawningTimes[i])

    print ("Elements scheduled for %s : %s"%(spawning_ground,o.elements_scheduled))

    #########################
    # Run the model
    #########################
    o.run(end_time=endTime, time_step=timedelta(hours=1),time_step_output=timedelta(hours=12), 
          outfile=outputFilename,export_variables=['lon', 'lat', 'z','sea_water_temperature','length','weight','survival','sea_floor_depth_below_sea_level']) 
    print (o)
    #o.animation(background=['x_sea_water_velocity', 'y_sea_water_velocity'],filename=animationFilename)

print(8)
#########################
# SETUP
#########################
spawning_ground='viking'
lowDepth, highDepth = -50, 0 # in negative meters
verticalBehavior=False

for year in range(2010, 2011):
    print(year)
#Spawning period and number of particles per spawning ground:
    if spawning_ground=='south':
        startTime=datetime(year-1,12,15,1,00,00) 
        endTime=datetime(year,8,15,1,00,00)  
        startSpawningTime=startTime
        endSpawningTime=datetime(year,4,15,1,00,00)
        releaseParticles=32400 # Total number of particles to release (result with be approximately this number)
    elif spawning_ground=='northwest':
        startTime=datetime(year,1,1,1,00,00) 
        endTime=datetime(year,9,29,1,00,00) 
        startSpawningTime=startTime
        endSpawningTime=datetime(year,5,1,1,00,00)
        releaseParticles=22950
    elif spawning_ground=='viking':
        startTime=datetime(year,2,1,1,00,00) 
        endTime=datetime(year,9,29,1,00,00) 
        startSpawningTime=startTime
        endSpawningTime=datetime(year,5,15,1,00,00)
        releaseParticles=27000
    else:
        print ("spawning_ground is not correctly defined")

#Find forcing files needed based on months:
    startDay = datetime(startTime.year,startTime.month,1)
    endDay = datetime(endTime.year,endTime.month,1)
    month_range = [startDay]
    while startDay<endDay:
        startDay = startDay + relativedelta(months=1)
        month_range.append(startDay)

    pattern_svim=[]
    for i in month_range:
        x='/Volumes/Untitled/ROMS_files/SVIM_compressed/'+str(i.year)+'/'+'ocean_avg_'+str(i.year)+str(i.month).zfill(2)+'01.nc4'
        pattern_svim.append(x)

    hoursBetweenTimestepInROMSFiles=24

    shapefile='/Volumes/Untitled/Sustain/Spawning_grounds/Shapefiles_Gio_KINO/'+str(spawning_ground)+'.shp'
    print ("=> Using shapefile %s"%(shapefile))
    outputFilename, animationFilename, plotFilename = createOutputFilenames(startTime,endTime,verticalBehavior,spawning_ground)
    print ("Result files will be stored as:\nnetCDF=> %s\nmp4=> %s"%(outputFilename,animationFilename))
              
    createAndRunSimulation(lowDepth,highDepth,endTime,shapefile,outputFilename,animationFilename,plotFilename,releaseParticles,pattern_svim,verticalBehavior,spawning_ground)

