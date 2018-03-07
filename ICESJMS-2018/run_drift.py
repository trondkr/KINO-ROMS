#!/usr/bin/env python

# This code runs the model pelagicplankton.py and was developed by Trond Kristiansen (me (at) trondkristiansen.com)
# and Kristina Kvile (kristokv (at) gmail.com)
# To run the model, include the files in this repository in the repository: github.com/OpenDrift/opendrift/

from datetime import datetime, timedelta
import numpy as np
from opendrift.readers import reader_basemap_landmask
from opendrift.readers import reader_ROMS_native
from kino.pelagicplankton import PelagicPlanktonDrift
from opendrift.readers import reader_netCDF_CF_generic
import logging
import gdal
import os
from netCDF4 import Dataset, datetime, date2num,num2date
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
    difference=endTime-startTime
    hoursOfSimulation=divmod(difference.total_seconds(), 3600)
    difference=endSpawningTime-startSpawningTime
    hoursOfSpawning=divmod(difference.total_seconds(), 3600)
    timeStepsSimulation=int(int(hoursOfSimulation[0])/hoursBetweenTimestepInROMSFiles)
		
    print "\nKINO TIME EVOLUTION:"
    print "=>SIMULATION: Drift simulation will run for %s simulation hours" %(timeStepsSimulation)
    print "=>SPAWNING: Simulated spawning will run for %s simulation hours\n initiated on %s and ending on %s"%(timeStepsSimulation,startSpawningTime,endSpawningTime)

    interval = timedelta(hours=24)
    hoursPerSpawning=divmod(interval.total_seconds(), 3600) #hours per spawning event
    timeStepsSpawning=int(int(hoursOfSpawning[0])/int(hoursPerSpawning[0])) #number of spawning timesteps
    spawningTimes = [startSpawningTime + interval*n for n in range(timeStepsSpawning)] #times of spawning

    # Normal distribution around 0.5
    mu, sigma = 0.5, 0.1 # mean and standard deviation
    prng = RandomState(1) # random number generator (specify number to ensure the same sequence each time)
    s = prng.normal(mu, sigma, len(spawningTimes)) # random distribution
    num=(s*releaseParticles).astype(int) # number of particles released per spawning event
    print num #timeStepsSpawning * releaseParticles * mu gives approx. number of particles released
    num=np.sort(num) #sort particles in increasing order 
    num=np.concatenate((num[len(num)%2::2],num[::-2]),axis=0) #release the highest number of particles at the midpoint of the spawning period
	
    print "SPAWNING: Simulated spawning will release %s eggs"%(np.sum(num))

    return num, spawningTimes


def createOutputFilenames(startTime,endTime,polygonIndex,specie,shapefile,verticalBehavior,resolution):
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
		outputFilename='results/%s_polygon_%s_%s_opendrift_%s_to_%s_vertical_test.nc'%(specie,polygonIndex,resolution,startDate,endDate)
    else:
		outputFilename='results/%s_polygon_%s_%s_opendrift_%s_to_%s_novertical_test.nc'%(specie,polygonIndex,resolution,startDate,endDate)
    if not os.path.exists('results'):
        os.makedirs('results')
    return outputFilename

   
def createAndRunSimulation(lowDepth,highDepth,endTime,layer,layerName,polygonIndex,shapefile,specie,outputFilename,releaseParticles,kinoDirectory,pattern_kino_orig,pattern_kino_new,pattern_kino_wind,svimDirectory,pattern_svim,forceDirectory,pattern_force,verticalBehavior,resolution):

    # Setup a new simulation
    o = PelagicPlanktonDrift(loglevel=0)  # Set loglevel to 0 for debug information

    #######################
    # Preparing readers
    #######################
    reader_basemap = reader_basemap_landmask.Reader(
                       llcrnrlon=-10, llcrnrlat=45,
                       urcrnrlon=20, urcrnrlat=75,
                       resolution='h', projection='merc')
    o.add_reader([reader_basemap]) 

    if resolution=='kino':
        reader_svim = reader_ROMS_native.Reader(svimDirectory+pattern_svim) #SVIM reader used to cover area outside KINO reader
        #For 2012: all variables contained in regular reader_kino:
        if startTime.year==2012:
            reader_kino = reader_ROMS_native.Reader([kinoDirectory+ s for s in pattern_kino_orig])
            o.add_reader([reader_kino,reader_svim]) 
        #For 2013: old and new KINO files with different format, must be read separately, wind information in separate file:
        elif startTime.year==2013:
            reader_kino_orig = reader_ROMS_native.Reader([kinoDirectory+ s for s in pattern_kino_orig])
            reader_kino_new = reader_ROMS_native.Reader([kinoDirectory+ s for s in pattern_kino_new])
            reader_kino_wind = reader_ROMS_native.Reader(kinoDirectory+pattern_kino_wind)
            #Specify which variables to read to avoid reading wind (empty):
            o.add_reader([reader_kino_orig,reader_kino_new,reader_svim],variables=['sea_floor_depth_below_sea_level', 'x_sea_water_velocity', 'y_sea_water_velocity','upward_sea_water_velocity', 'sea_water_temperature','sea_water_salinity'])
            o.add_reader([reader_kino_wind])
        else:
            print "Unknown format of KINO files"
        
    elif resolution=='svim':
        reader_svim = reader_ROMS_native.Reader(svimDirectory+pattern_svim)
        reader_svim_force = reader_ROMS_native.Reader(forceDirectory+pattern_force)
        o.add_reader([reader_svim,reader_svim_force]) #FORCE loaded for wind information
    else:
        print "Resolution is not correctly defined"
    
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
    o.set_config('turbulentmixing:verticalresolution', 2) # meter
    if verticalBehavior:
	    o.set_config('processes:verticaladvection', False)
    else:
		o.set_config('processes:verticaladvection', False)
    o.set_config('turbulentmixing:TSprofiles', False)
    o.set_config('turbulentmixing:max_iterations', 200) 
    o.set_config('drift:scheme', 'euler')
    o.set_config('general:coastline_action', 'previous') #Prevent stranding, jump back to previous position
    o.set_config('general:basemap_resolution', 'h')


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
        print "Running i=%s num=%s for species=%s and polygon=%s"%(i,nums,layerName,polygonIndex)
        print "Depths ",np.repeat(z_levels,z_dist)
        o.seed_from_shapefile(shapefile, nums, layername=specie,featurenum=[polygonIndex], z=np.repeat(z_levels,z_dist), time=spawningTimes[i])

	print "Elements scheduled for %s : %s"%(specie,o.elements_scheduled)

    #########################
    # Run the model
    #########################
    o.run(end_time=endTime, time_step=timedelta(hours=1),time_step_output=timedelta(hours=2), #output 2hrs in old version
          outfile=outputFilename) 
    print o

#########################
# SETUP IBM
#########################
resolution='svim' # 'svim'=low resolution ocean model, 'kino'=high resolution ocean model

startTime=datetime(2012,1,15,1,30,05) 
endTime=datetime(2012,8,15,1,30,05) 

startSpawningTime=startTime 
endSpawningTime=datetime(2012,4,20,1,30,05)
releaseParticles=220 # Number of particles released per timestep, multiplied by gaussian bell (so maximum is releaseParticles and minimum is close to zero)
lowDepth, highDepth = -30, 0 # Upper and lower release depth 
verticalBehavior=True # Defines if vertical mixing and larval behaviour is turned on

if resolution=='kino':
    hoursBetweenTimestepInROMSFiles=3
elif resolution=='svim':
    hoursBetweenTimestepInROMSFiles=24
else:
    print "Resolution is not correctly defined"


#SVIM: 4KM, 24H resolution:
svimDirectory='/Volumes/Untitled/ROMS_files/SVIM_compressed/'+str(startTime.year)+'/' #Directory for SVIM files
pattern_svim='ocean_avg_*.nc4' 
#Ocean force: wind information from model forcing. Missing in SVIM files
forceDirectory='/Volumes/Untitled/ROMS_files/SVIM_force/'+str(startTime.year)+'/' #Directory for wind files 
pattern_force='ocean_force_*.nc'

#KINO: 1.6 KM, 2H resolution. Files named after ROMS time, only read needed files:
kinoDirectory='/Volumes/Untitled/ROMS_files/KINO_compressed/'+str(startTime.year)+'/' 
#Empty arrays to store names of needed files:
pattern_kino_new=[]
pattern_kino_orig=[]
pattern_kino_wind='NORTHSEA_Vwind_2013_2015.nc' #Wind only needed in 2013

#For 2012: all variables contained in KINO forcing files, all files same format:
if startTime.year==2012:
    firstkino = int(date2num(startTime,units="days since 1948-01-01 00:00:00",calendar="standard"))-1
    lastkino = int(date2num(endTime,units="days since 1948-01-01 00:00:00",calendar="standard"))+1
    for i in range(firstkino,lastkino+1):
        x='kino_1600m_'+str(i)+'.nc4'
        pattern_kino_orig.append(x)

#For 2013: old and new KINO files with different format, must be read separately, wind information in separate file:
elif startTime.year==2013:
    for i in range(23754,23849):
        x='kino_1600m_'+str(i)+'.nc4'
        pattern_kino_orig.append(x)
    for i in range(23830,23970):
        x='kino_1600m_'+str(i)+'.nc'
        pattern_kino_new.append(x)

else:
    print "Unknown format of KINO files"
        
    
# Get spawning grounds from shapefile:
specie='Torsk_28102016_wgs84'
shapefile='shapefiles/'+str(specie)+'.shp'
s = ogr.Open(shapefile)

#Loop through the layers in s (only 1)
for layer in s:
    #polygons=[1,2,3,4,7] #N.Trench,Dogger bank C, Dogger bank, German bight, Viking bank
    polygons=[1]
    for polygonIndex in polygons:
        feature = layer.GetFeature(polygonIndex-1)
        geom = feature.GetGeometryRef()
        points = geom.GetGeometryCount()
        ring = geom.GetGeometryRef(0)
        if ring.GetPointCount() > 3:
            outputFilename = createOutputFilenames(startTime,endTime,polygonIndex,specie,shapefile,verticalBehavior,resolution)
            print "Result files will be stored as:\nnetCDF=> %s"%(outputFilename)

            createAndRunSimulation(lowDepth,highDepth,endTime,layer,specie,polygonIndex,shapefile,
                    specie,outputFilename,releaseParticles,
                    kinoDirectory,pattern_kino_orig,pattern_kino_new,pattern_kino_wind,svimDirectory,pattern_svim,forceDirectory,pattern_force,verticalBehavior,resolution)

