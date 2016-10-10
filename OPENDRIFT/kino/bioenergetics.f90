Module bioenergetics

  !
  ! ---------------------------------------------------------------
  ! This module calculates the bioenergetics for larval cod such as metabolism
  ! 
  ! To run this on Hecxagon do this first:
  !
  ! module swap PrgEnv-pgi PrgEnv-gnu
  ! 
  ! f2py --verbose -c -m bioenergetics bioenergetics.f90
  !
  ! email : me (at) trondkristiansen.com
  ! ---------------------------------------------------------------
  !
  ! USAGE:
  ! ---------------------------------------------------------------------------------------------------------------------------------------------------

  Implicit None

  ! f2py --verbose -c -m bioenergetics bioenergetics.f90"

Contains

  Subroutine growth (larvamm,larvawgt,stomach,ingestionrate,&
    &growthrateInPercent,stomachFullness,haddock,&
    &activemetabOn,constantIngestion,fractionOfTimestepSwimming,Eb,dt,temp)

    real(kind=8) meta, larvamm, temp, larvawgt,larvawgt_previous
    real(kind=8) maxgrowthrateInPercent,maxgrowthrateInMG,assi,stomachFullness
    real(kind=8) constantIngestion,activityCost,growthrateInPercent,swimspeed
    real(kind=8) Eb,maxg,ingestionrate,stomach,stomach_previous,larvamm_previous
    real(kind=8) fractionOfTimestepSwimming ! swimdistance is the fraction of &
    ! maximum distance allowed to swim in one timestep. Scales cost of swimming with no swimming

    Integer dt,activemetabOn,haddock

    double precision :: ingestion,swimdistance

!f2py intent(in,out,overwrite) larvamm,larvawgt,stomach,ingestionrate,growthrateInPercent,stomachFullness
!f2py intent(in) haddock,activemetabOn,constantIngestion,swimdistance,Eb,deltaH,dt,temp


    ! NOTE: input units to this subroutine is larval_weight in mg. Output
    ! converted to microgram.

    real(kind=8),parameter:: mm2m  = 0.001
    real(kind=8),parameter:: m2mm  = 1000.
    real(kind=8),parameter:: ltr2mm3 = 1e-6
    real(kind=8),parameter:: ug2mg = 0.001
    real(kind=8),parameter:: mg2ug=1000.0
    real(kind=8),parameter:: sec2day = 1.0/86400.0
    real(kind=8),parameter:: gut_size=0.05
    real(kind=8),parameter:: costRateOfMetabolism=0.5 
    ! The rate of how much full swimming for one time step 
    ! will cost relative to routine metabolism
    
    if (haddock==1) then
        ! Equation taken from Petrik et al. 2009 (Equation 4).
        ! I convert from uL O2 h-1 to ug h-1 using the following formulation:
        ! 4.184 J/cal *4.8 cal/ml 02 * 1e-3 ml/uL* 1/(13560 J/g 02) *1e6 ug/g*x
        ! uL/hr or multiple  x uL/hr by 1.481062 ug/uL 02  to get ug/hr
        !
        ! resp=(resp*1.481062)
        ! Input for Lankin metabolism is wight in mg
        meta = dt*sec2day*(1.021*((larvawgt)**(0.979))*exp(0.092*temp)) / 3600.
        ! Convert metabolism uL O2 h-1 to ug h-1
        meta = meta*1.48106
        !print*,"Metabolism for haddock :",meta, (meta/(Larval_wgt*mg2ug))*100.
        ! Finn et al. 2002
        !print*,"Metabolism for cod  1  :",dt*2.38e-7*exp(0.088*Tdata)*((Larval_wgt)**(0.9))*deltaH*mg2ug, Larval_wgt
        ! Lough et al. 2005
        !print*,"Metabolism for cod  2  :",(0.00114*((Larval_wgt*mg2ug)**(1.029-0.00774*log(Larval_wgt*mg2ug)))*exp(Tdata*(0.10720-0.0032*log(Larval_wgt*mg2ug))))*1.48106 !*1.481062e-12
    else
        ! Assume cod as default
        meta=(dt*sec2day/3600.)*(0.00114*((larvawgt*mg2ug)**(1.029-0.00774&
          &*log(larvawgt*mg2ug)))*exp(temp*(0.10720-0.0032*log(larvawgt*mg2ug))))*1.48106
        !print*,"metabolism is cod",meta
       ! meta = dt*2.38e-7*exp(0.088*Tdata)*((Larval_wgt)**(0.9))*deltaH*mg2ug
    end if
    ! Convert ug h-1 to mg h-1
    meta=meta*ug2mg

    ! Increase metabolism during active hours (light above threshold) Lough et  al. 2005
    if (activemetabOn > 0) then
        if (Eb > 0.001) then
            if (larvamm > 5.5) then
                meta = (2.5*meta)
            else
                meta = (1.4*meta)
            end if
        end if
    end if
    !Calculate assimilation efficiency
    assi=0.8*(1-0.400*exp(-0.002*(larvawgt*mg2ug-50.0)))
    ! Calculate daily growth rate (SGR in percent %)
    maxgrowthrateInPercent = 1.08 + 1.79*temp - 0.074*temp*log(larvawgt) &
        &- 0.0965*temp*log(larvawgt)**2 &
        &+ 0.0112*temp*log(larvawgt)**3

    ! Growth rate (g) converted to milligram weight (GR_mg) per timestep:
    !g =  (log((GR+0.0000000001)/100.+1))*sec2day*dt*deltaH
    !print*,"correct: does this fix it",g, meta, assi, Tdata, Larval_wgt
    ! TODO:
    ! In some rare cases with very cold water which is outside the limnits
    ! of this function, I got values for GR less than 1. Taking the log of less than 1
    ! or 0 gives inf (nan) values. I added a check (max(0.0,GR)) to avoid this
    ! problem. But this should be fixed...
    maxg =  max(0.0,(dlog(maxgrowthrateInPercent/100.+1))*sec2day*dt)
    
    maxgrowthrateInMG=(larvawgt*(Exp(maxg)-1.))

    ! No ingestion if light is too low
    if (Eb > 0.001) then
      ingestion = (constantIngestion*larvawgt*gut_size)
    else
      ingestion=0.0
    end if

    ! Calculate stomach fullness
    stomach_previous=stomach
    stomachFullness =  min(1.0,(stomach_previous + &
      &ingestion/(larvawgt*gut_size)))
   
    ! Calculate how far the larva can swim in one timestep
    swimspeed=0.261*(larvamm**(1.552*larvamm**(0.920-1.0)))-(5.289/larvamm)
    ! Distance in one time step divided by 2 to account for other activities
    swimdistance=(swimspeed*dt)*fractionOfTimestepSwimming
       
    !Calculate the cost of being active. The more you swim the more you use energy in raltive ratio to
    !routine metabolims. Trond Kristiansen, 23.03.2010"""
    activityCost= (swimdistance*meta*costRateOfMetabolism)

    ! Calculate stomach content, ingestionrate, and larval weight
    stomach=max(0.0, min(gut_size*larvawgt, stomach_previous + ingestion))

    ingestionrate=max(0.0, (stomach-stomach_previous)/larvawgt)*100.

    larvawgt_previous=larvawgt
    larvawgt=larvawgt+min(maxgrowthrateInMG + meta, stomach*assi) &
    &- meta - activityCost
    
    growthrateInPercent=((larvawgt-larvawgt_previous)/larvawgt_previous)*100. 
  
    larvamm_previous=larvamm
    larvamm = exp(2.296 + 0.277*log(larvawgt) - 0.005128*log(larvawgt)**2)
    if (larvamm < larvamm_previous) then
        larvamm = larvamm_previous
    end if
   ! write(*,*) "wgt:",larvawgt, "grow rate:",growthrateInPercent,maxgrowthrateInPercent
   
    return

    end subroutine growth

end module bioenergetics