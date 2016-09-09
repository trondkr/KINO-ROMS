
Module calclight
        implicit none
        ! Calculate light in the ocean (based on HYCOM modules)
        ! module swap PrgEnv-pgi PrgEnv-gnu
        ! module unload notur
        ! f2py --verbose -c -m calclight calclight.f90
        !
        ! email : me (at) trondkristiansen.com

        contains

            subroutine qsw(radfl0,radmax,cawdir,clouds,rlat,time,daysinyear,num)
            ! This subroutine get max irradiance for day, latitude, clouds (HYCOM)
            ! -------------------------------------------------------------------------------------------
            ! USAGE: call qsw0(radfl0,radmax,cawdir,clouds,lat*pi/180.0,time,daysinyear,num)
            !
            ! WHERE: pi      = 4.0*atan(1.0)
            !        clouds  = 0.0
            !        rlat    = lat*pi/180.0
            !        time    = 1.0:365
            !        daysinyear=365.0
            !        n = number of individual lats
            ! -------------------------------------------------------------------------------------------
            ! radfl0 (out) - 24 hrs mean solar irrradiance at the marine surface layer --- (unit: w/m^2)
            ! radmax (out) - daily maximum solar irrradiance at the marine surface layer --- (unit: w/m^2)
            ! cawdir (out) - not sure what this is
            ! clouds (in)     - cloud input (fraction of cloudy sky)
            ! rlat (in)       - latitude (radians)
            ! time (in)       - julian day
            ! daysinyear (in) - number of days in the year
            ! n - number of positions to calculate

                  real, dimension(num):: cawdir,radfl0,radmax,rlat
                  real, dimension(num):: sdir,sdif,altdeg,cfac,ssurf,stot
                  real, dimension(num):: sin2,cos2,cosz,scosz,srad

                  real, intent(in) :: time, clouds
                  integer, intent(in) :: daysinyear, num

                  real  pi2,deg,rad,eepsil
                  integer ifrac,npart
                  real  fraci,absh2o,s0,day,dangle,decli,sundv
                  real  cc,bioday,biohr,hangle
                  
!f2py intent(in) clouds,rlat,time,daysinyear,num
!f2py intent(in,out,overwrite) radfl0,radmax,cawdir

            ! --- -------------------------------------------------------------------
            ! --- compute 24 hrs mean solar irrradiance at the marine surface layer
            ! --- (unit: w/m^2)
            ! --- -------------------------------------------------------------------

            ! --- set various quantities

                  !print *,'calling qsw0'
                  pi2=8.*atan(1.)          !        2 times pi
                  deg=360./pi2             !        convert from radians to degrees
                  rad=pi2/360.             !        convert from degrees to radians
                  eepsil=1.e-9             !        small number

                  ifrac=24                 !        split each 12 hrs day into ifrac parts
                  fraci=1./real(ifrac)     !        1 over ifrac

                  absh2o=0.09              ! ---    absorption of water and ozone
                  s0=1365.                 ! w/m^2  solar constant


           
            ! --- -------------------------------------------------------------------
            ! --- compute 24 hrs mean solar radiation at the marine surface layer
            ! --- -------------------------------------------------------------------

            !KAL  ttime=time+dt/86400.
            !KAL? day=aint(time*365./360.)          !accumulated day number (jan1=0,364,..)
                  !day=aint(time/float(daysinyear))  !accumulated day number (jan1=0,364,..)
                  day=amod(time,float(daysinyear))    !0 < day < 364
                  day=floor(day)
                  dangle=pi2*day/float(daysinyear)   !day-number-angle, in radians
                  if (day<0. .or. day>daysinyear+1) then
                     print *,'qsw0: Error in day for day angle'
                     print *,'Day angle is ',day,daysinyear
                     stop
                  end if

            ! --- compute astronomic quantities --
                  decli=.006918+.070257*sin(dangle)   -.399912*cos(dangle) &
                              +.000907*sin(2.*dangle)-.006758*cos(2.*dangle) &
                              +.001480*sin(3.*dangle)-.002697*cos(3.*dangle)

                  sundv=1.00011+.001280*sin(dangle)   +.034221*cos(dangle) &
                              +.000077*sin(2.*dangle)+.000719*cos(2.*dangle)

            ! --- compute cloudiness fraction

            ! KAL cc=clouds(i,j,l0)*w0+clouds(i,j,l1)*w1
            ! KAL.  +clouds(i,j,l2)*w2+clouds(i,j,l3)*w3
                  cc = clouds

            ! --- compute astronomic quantities

                  sin2=sin(rlat)*sin(decli)
                  cos2=cos(rlat)*cos(decli)

            ! --- split each day into ifrac parts, and compute the solar radiance for
            ! --- each part. by assuming symmetry of the irradiance about noon, it
            ! --- is sufficient to compute the irradiance for the first 12 hrs of
            ! --- the (24 hrs) day (mean for the first 12 hrs equals then the mean
            ! --- for the last 12 hrs)

                  scosz=0.
                  stot=0.
                  radmax=0.0

                  do npart=1,ifrac
                     bioday=day+(npart-.5)*fraci*.5
                     biohr=bioday*86400.                !hour of day in seconds
                     biohr=amod(biohr+43200.,86400.)    !hour of day;  biohr=0  at noon
                     hangle=pi2*biohr/86400.            !hour angle, in radians
                     cosz=amax1(0.,sin2+cos2*cos(hangle)) !cosine of the zenith angle
                     scosz=scosz+cosz                     !  ..accumulated..

                     srad =s0*sundv*cosz                  !extraterrestrial radiation

                     !print *,i,j,npart,srad,cosz,eepsil
                     ! obs: .7^100 = 3x10^-16 , an already ridicolously low number ...
                     sdir=srad*0.7**(min(100.,1./(cosz+eepsil)))    !direct radiation component
            !         sdir=srad*0.7**(1./(cosz+eepsil))    !direct radiation component
            !         sdir=srad * exp(-0.356674943938732447/(cosz+eepsil))

                     sdif=((1.-absh2o)*srad-sdir)*.5      !diffusive radiation component

                     altdeg=amax1(0.,asin(min(1.0,sin2+cos2)))*deg !solar noon altitude in degrees


                     cfac=(1.-0.62*cc+0.0019*altdeg)      !cloudiness correction

                     ssurf=(sdir+sdif)*cfac
                     radmax=max(radmax,ssurf)
                     stot=stot+ssurf
                  enddo
                  scosz=scosz*fraci                    !24-hrs mean of  cosz
                  radfl0=stot*fraci               !24-hrs mean shortw rad in w/m^2


                  cawdir=1.-amax1(0.15,0.05/(scosz+0.15))
                 ! print *,time,day,dangle,decli,sundv !,radfl0(63,95)
                                                       !co-albedo over water for dir light
                  end subroutine qsw


           !     -------------------------------------------------
                  SUBROUTINE SURLIG(H,MAXLIG,D,B,HEIGHT,SLIG)
            !     -------------------------------------------------
            !   Surface irradiance after Skartveit & Olseth 1988
                      implicit none
                  REAL     B,D,DELTA,HEIGHT,H,P,V,MAXLIG
                  REAL     SLIG,H12,TWLIGHT, DEG2RAD
            
                    
!f2py intent(in,overwrite) H,MAXLIG,D,B
!f2py intent(in,out,overwrite) HEIGHT,SLIG

            !     B:Degrees north
            !     DELTA: sun declination
            !     D: day of the year
            !     H: hour of day
            !     HEIGHT: sin(sunheight)
            !     IRR. irradiance above sea surface uEm-2s-1
            !     P: Pi
            !     R: factor for distance variations between sun-earth 
            !     SLIG:surface light
            !     V: sunheight in degrees
            !     TWLIGHT: light at 0-degree sun
            !   MAXLIG: level of irradiance at midday
            
                  P = 3.1415927
                  TWLIGHT = 5.76
                  DEG2RAD=(3.14152/180.0)
                  
                    DELTA = .3979*SIN(DEG2RAD*.9856*(D-80)+    &
                        1.9171*(SIN(.9856*D*DEG2RAD)-.98112))
                            H12 = DELTA*SIN(B*1.*DEG2RAD)-         &
                          SQRT(1.-DELTA**2)*COS(B*1.*DEG2RAD)*COS(15.*12*DEG2RAD)
            
                    HEIGHT = DELTA*SIN(B*1.*DEG2RAD)-          &
                             SQRT(1.-DELTA**2)*COS(B*1.*DEG2RAD)*COS(15.*H*DEG2RAD)
                            
                    V = ASIN(HEIGHT*DEG2RAD)
                             
                      IF (V .GE. 0.) THEN                  
                        SLIG = MAXLIG*(HEIGHT/H12) + TWLIGHT
                      ELSE IF (V .GE. -6.) THEN
                        SLIG = ((TWLIGHT - .048)/6.)*(6.+V)+.048 
                      ELSE IF (V .GE. -12.) THEN
                        SLIG = ((.048 - 1.15E-4)/6.)*(12.+V)+1.15E-4
                      ELSE IF (V .GE. -18) THEN
                        SLIG = (((1.15E-4)-1.15E-5)/6.)*(18.+V)+1.15E-5
                      ELSE 
                        SLIG = 1.15E-5
                      ENDIF
            
              
                    !WRITE(*,800)D,H,HEIGHT/H12,HEIGHT
            
        !    800   FORMAT(I4,3X,F5.2,3X,2(F15.10,2X))
            
            
                  RETURN
                  
                  end subroutine surlig
                  



end module calcLight