# This file is part of OpenDrift.
#
# OpenDrift is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# OpenDrift is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenDrift.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2015, Knut-Frode Dagestad, MET Norway

import os
import numpy as np
from datetime import datetime, timedelta

from opendrift.models.opendrift3D import OpenDrift3DSimulation, Lagrangian3DArray
from opendrift.elements import LagrangianArray

# Necessary to import the Fortran module that calculates light
import calclight
import bioenergetics

# Defining the oil element properties
class PelagicPlankton(Lagrangian3DArray):
    """Extending Lagrangian3DArray with specific properties for pelagic eggs
    """

    variables = LagrangianArray.add_variables([
        ('diameter', {'dtype': np.float32,
                      'units': 'm',
                      'default': 0.0014}),  # for NEA Cod
        ('neutral_buoyancy_salinity', {'dtype': np.float32,
                                       'units': '[]',
                                       'default': 31.25}),  # for NEA Cod
        ('density', {'dtype': np.float32,
                     'units': 'kg/m^3',
                     'default': 1028.}),
        ('age_seconds', {'dtype': np.float32,
                         'units': 's',
                         'default': 0.}),
        ('hatched', {'dtype': np.int64,
                     'units': '',
                     'default': 0}),
        ('stage_fraction', {'dtype': np.float32,   #KK: Added to track percentage of development time completed
                         'units': '',
                         'default': 0.}),               
        ('length', {'dtype': np.float32,
                         'units': 'mm',
                         'default': 4.0}),
        ('weight', {'dtype': np.float32,
                         'units': 'mg',
                         'default': 0.08}),
        ('Eb', {'dtype': np.float32,
                     'units': 'ugEm2',
                     'default': 0.}),
         ('light', {'dtype': np.float32,
                     'units': 'ugEm2',
                     'default': 0.}),
         ('growth_rate', {'dtype': np.float32,   
                          'units': '%',
                          'default': 0.}),
         ('ingestion_rate', {'dtype': np.float32,   
                          'units': '%',
                          'default': 0.}),
         ('stomach_fullness', {'dtype': np.float32, 
                          'units': '%',
                          'default': 0.}),
         ('stomach', {'dtype': np.float32, 
                          'units': '',
                          'default': 0.}),
         ('survival', {'dtype': np.float32, 
                          'units': '',
                          'default': 1.})])

    


    def calculateMaximumDailyLight(self):
        """LIGHT == Get the maximum light at the current latitude, and the current surface light at the current time.
        These values are used in calculateGrowth and  predation.FishPredAndStarvation, but need only be calcuated once per time step. """

        tt = self.time.timetuple()
      
        num=np.shape(self.elements.lat)[0]
        dayOfYear = float(tt.tm_yday); month=float(tt.tm_mon); hourOfDay = float(tt.tm_hour); daysInYear=365.0
        radfl0=np.zeros((num)); maxLight=np.zeros((num)); 
        cawdir=np.zeros((num)); clouds=0.0; 
        sunHeight=np.zeros((num)); surfaceLight=np.zeros((num))

        """Calculate the maximum and average light values for a given geographic position
        for a given time of year. Notice we use radfl0 instead of maximum values maxLight
        in light caclualtions. Seemed better to use average values than extreme values.
        NOTE: Convert from W/m2 to umol/m2/s-1"""
        radfl0,maxLight,cawdir = calclight.calclight.qsw(radfl0,maxLight,cawdir,clouds,self.elements.lat*np.pi/180.0,dayOfYear,daysInYear,num)
        maxLight = radfl0/0.217
        """Calculate the daily variation of irradiance based on hour of day - store in self.elements.light"""
        for ind in xrange(len(self.elements.lat)):
        
          sunHeight, surfaceLight = calclight.calclight.surlig(hourOfDay,float(maxLight[ind]),dayOfYear,float(self.elements.lat[ind]),sunHeight,surfaceLight)
          self.elements.light[ind]=surfaceLight

    def updateSurvival(self):
        # Update the size dependent mortality
        aPred = 1.78e-5
        bPred = -1.3 
        mortality = aPred*(self.elements.length**bPred)*(self.time_step.total_seconds()/3600.)
        self.elements.survival = self.elements.survival*(np.exp(-mortality))

    def updateEggDevelopment(self):
        # Update percentage of egg stage completed
        amb_duration = np.exp(3.65 - 0.145*self.environment.sea_water_temperature) #Total egg development time (days) according to ambient temperature (Ellertsen et al. 1988)
        days_in_timestep = self.time_step.total_seconds()/(60*60*24)  #The fraction of a day completed in one time step
        amb_fraction = days_in_timestep/(amb_duration) #Fraction of development time completed during present time step 
        self.elements.stage_fraction += amb_fraction #Add fraction completed during present timestep to cumulative fraction completed
        self.elements.hatched[self.elements.stage_fraction>=1] = 1 #Eggs with total development time completed are hatched (1)

    def updateVertialPosition(self,length,oldLight,currentLight,currentDepth,stomach_fullness,dt):
        # Update the vertical position of the current larva
        swimSpeed=0.261*(length**(1.552*length**(0.920-1.0)))-(5.289/length)
        fractionOfTimestepSwimming = self.config['biology']['fractionOfTimestepSwimming']
        maxHourlyMove = swimSpeed*fractionOfTimestepSwimming*dt
        maxHourlyMove =  round(maxHourlyMove/1000.,1) # depth values are negative
        lowerStomachLim = self.config['biology']['lowerStomachLim']

        if (oldLight <= currentLight and stomach_fullness >= lowerStomachLim): #If light increases and stomach is sufficiently full, go down
          depth = min(0.0,currentDepth - maxHourlyMove)
        else: #If light decreases or stomach is not sufficiently full, go up
          depth = min(0,currentDepth + maxHourlyMove)
        #print "current depth %s new depth %s light %s lastLight %s"%(currentDepth,depth,currentLight,oldLight)
        #print "maximum mm to move %s new depth %s old depth %s"%(maxHourlyMove,depth,currentDepth)
        return depth

    def updatePlanktonDevelopment(self):
   
        constantIngestion = self.config['biology']['constantIngestion']
        activemetabOn = self.config['biology']['activemetabOn']
        attCoeff = self.config['biology']['attenuationCoefficient']
        haddock = self.config['biology']['haddock']
        fractionOfTimestepSwimming = self.config['biology']['fractionOfTimestepSwimming']

        self.updateEggDevelopment()
        
        # Save the light from previous timestep to use for vertical behavior
        lastLight=np.zeros(np.shape(self.elements.light))
        lastLight[:]=self.elements.light[:]

        self.calculateMaximumDailyLight()

        self.elements.Eb=self.elements.light*np.exp(attCoeff*(self.elements.z))
     
        dt=self.time_step.total_seconds()

        for ind in xrange(len(self.elements.lat)):
          if (self.elements.hatched[ind]>=1):
          # Calculate biological properties of the individual larva                                 
            larvamm,larvawgt,stomach,ingrate,growthrate,sfullness=bioenergetics.bioenergetics.growth(self.elements.length[ind],
              self.elements.weight[ind],
              self.elements.stomach[ind],
              self.elements.ingestion_rate[ind],
              self.elements.growth_rate[ind],
              self.elements.stomach_fullness[ind],
              haddock,
              activemetabOn,
              constantIngestion,
              fractionOfTimestepSwimming,
              self.elements.Eb[ind],
              dt,
              self.environment.sea_water_temperature[ind])
            # Update the element

            self.elements.length[ind]=larvamm
            self.elements.weight[ind]=larvawgt
            self.elements.stomach[ind]=stomach
            self.elements.ingestion_rate[ind]=ingrate
            self.elements.growth_rate[ind]=growthrate
            self.elements.stomach_fullness[ind]=sfullness

            self.elements.z[ind] = self.updateVertialPosition(self.elements.length[ind],
              lastLight[ind],
              self.elements.light[ind],
              self.elements.z[ind],
              self.elements.stomach_fullness[ind],
              dt)
         

class PelagicPlanktonDrift(OpenDrift3DSimulation,PelagicPlankton):
    """Buoyant particle trajectory model based on the OpenDrift framework.

        Developed at MET Norway

        Generic module for particles that are subject to vertical turbulent
        mixing with the possibility for positive or negative buoyancy

        Particles could be e.g. oil droplets, plankton, or sediments

        Under construction.
    """

    ElementType = PelagicPlankton

    required_variables = ['x_sea_water_velocity', 'y_sea_water_velocity',
                          'sea_surface_wave_significant_height',
                          'sea_surface_wave_to_direction',
                          'sea_ice_area_fraction',
                          'x_wind', 'y_wind', 'land_binary_mask',
                          'sea_floor_depth_below_sea_level',
                          'ocean_vertical_diffusivity',
                          'sea_water_temperature',
                          'sea_water_salinity',
                          'surface_downward_x_stress',
                          'surface_downward_y_stress',
                          'turbulent_kinetic_energy',
                          'turbulent_generic_length_scale',
                          'upward_sea_water_velocity'
                          ]

    # Vertical profiles of the following parameters will be available in
    # dictionary self.environment.vertical_profiles
    # E.g. self.environment_profiles['x_sea_water_velocity']
    # will be an array of size [vertical_levels, num_elements]
    # The vertical levels are available as
    # self.environment_profiles['z'] or
    # self.environment_profiles['sigma'] (not yet implemented)
    required_profiles = ['sea_water_temperature',
                         'sea_water_salinity',
                         'ocean_vertical_diffusivity']
    required_profiles_z_range = [-150, 0]  # The depth range (in m) which
                                          # profiles shall cover

    fallback_values = {'x_sea_water_velocity': 0,
                       'y_sea_water_velocity': 0,
                       'sea_surface_wave_significant_height': 0,
                       'sea_surface_wave_to_direction': 0,
                       'sea_ice_area_fraction': 0,
                       'x_wind': 0, 'y_wind': 0,
                       'sea_floor_depth_below_sea_level': 100,
                       'ocean_vertical_diffusivity': 0.02,  # m2s-1
                       'sea_water_temperature': 10.,
                       'sea_water_salinity': 34.,
                       'surface_downward_x_stress': 0,
                       'surface_downward_y_stress': 0,
                       'turbulent_kinetic_energy': 0,
                       'turbulent_generic_length_scale': 0,
                       'upward_sea_water_velocity': 0
                       }

    # Default colors for plotting
    status_colors = {'initial': 'green', 'active': 'blue',
                     'hatched': 'red', 'eaten': 'yellow', 'died': 'magenta'}

    # Configuration
    configspec = '''
        [drift]
            scheme = string(default='euler')
        [processes]
            turbulentmixing = boolean(default=True)
            verticaladvection = boolean(default=False)
        [turbulentmixing]
            timestep = float(min=0.1, max=3600, default=1.)
            verticalresolution = float(min=0.01, max=10, default = 1.)
            diffusivitymodel = string(default='environment')
        [biology]
             constantIngestion = float(min=0.0, max=1.0, default=0.5)
             activemetabOn = float(min=0, max=1, default=1)
             attenuationCoefficient = float(min=0.0, max=1.0, default=0.18)
             haddock = boolean(default=False)
             cod = boolean(default=True)
                   
    '''


    def __init__(self, *args, **kwargs):

        # Calling general constructor of parent class
        super(PelagicPlanktonDrift, self).__init__(*args, **kwargs)


    def update_terminal_velocity(self, Tprofiles=None, Sprofiles=None, z_index=None):
        """Calculate terminal velocity for Pelagic Egg

        according to
        S. Sundby (1983): A one-dimensional model for the vertical distribution
        of pelagic fish eggs in the mixed layer
        Deep Sea Research (30) pp. 645-661

        Method copied from ibm.f90 module of LADIM:
        Vikebo, F., S. Sundby, B. Aadlandsvik and O. Otteraa (2007),
        Fish. Oceanogr. (16) pp. 216-228
        """
        g = 9.81  # ms-2

        # Pelagic Egg properties that determine buoyancy
        eggsize = self.elements.diameter  # 0.0014 for NEA Cod
        eggsalinity = self.elements.neutral_buoyancy_salinity
        # 31.25 for NEA Cod


        # prepare interpolation of temp, salt
        if not (Tprofiles==None and Sprofiles==None):
            if z_index==None:
                z_i = range(Tprofiles.shape[0]) # evtl. move out of loop
                z_index = interp1d(-self.environment_profiles['z'],z_i,bounds_error=False) # evtl. move out of loop
            zi = z_index(-self.elements.z)
            upper = np.maximum(np.floor(zi).astype(np.int), 0)
            lower = np.minimum(upper+1, Tprofiles.shape[0]-1)
            weight_upper = 1 - (zi - upper)

        # do interpolation of temp, salt if profiles were passed into this function, if not, use reader by calling self.environment
        if Tprofiles==None:
            T0 = self.environment.sea_water_temperature
        else:
            T0 = Tprofiles[upper, range(Tprofiles.shape[1])] * weight_upper + Tprofiles[lower, range(Tprofiles.shape[1])] * (1-weight_upper) 
        if Sprofiles==None:
            S0 = self.environment.sea_water_salinity
        else:
            S0 = Sprofiles[upper, range(Sprofiles.shape[1])] * weight_upper + Sprofiles[lower, range(Sprofiles.shape[1])] * (1-weight_upper) 

        # The density difference bettwen a pelagic egg and the ambient water
        # is regulated by their salinity difference through the
        # equation of state for sea water.
        # The Egg has the same temperature as the ambient water and its
        # salinity is regulated by osmosis through the egg shell.
        DENSw = self.sea_water_density(T=T0, S=S0)
        DENSegg = self.sea_water_density(T=T0, S=eggsalinity)
        dr = DENSw-DENSegg  # density difference

        # water viscosity
        my_w = 0.001*(1.7915 - 0.0538*T0 + 0.007*(T0**(2.0)) - 0.0023*S0)
        # ~0.0014 kg m-1 s-1

        # terminal velocity for low Reynolds numbers
        W = (1.0/my_w)*(1.0/18.0)*g*eggsize**2 * dr

        #check if we are in a Reynolds regime where Re > 0.5
        highRe = np.where(W*1000*eggsize/my_w > 0.5)

        # Use empirical equations for terminal velocity in
        # high Reynolds numbers.
        # Empirical equations have length units in cm!
        my_w = 0.01854 * np.exp(-0.02783 * T0)  # in cm2/s
        d0 = (eggsize * 100) - 0.4 * \
            (9.0 * my_w**2 / (100 * g) * DENSw / dr)**(1.0 / 3.0)  # cm
        W2 = 19.0*d0*(0.001*dr)**(2.0/3.0)*(my_w*0.001*DENSw)**(-1.0/3.0)
        # cm/s
        W2 = W2/100.  # back to m/s

        W[highRe] = W2[highRe]
        self.elements.terminal_velocity = W


    def update(self):
        """Update positions and properties of buoyant particles."""

        # Update element age
        self.elements.age_seconds += self.time_step.total_seconds()

        # Turbulent Mixing
        self.update_terminal_velocity()
        
        self.updatePlanktonDevelopment()
        self.updateSurvival()

        # Horizontal advection
        self.advect_ocean_current()
       
        # Vertical advection
        if self.config['processes']['verticaladvection'] is True:
            self.vertical_advection()

        # Deactivate elements hitting land
        self.deactivate_stranded_elements()
