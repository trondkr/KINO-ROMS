#include "cppdefs.h"
#if defined NONLINEAR && defined SOLVE3D && (defined OFFLINE)
      SUBROUTINE main3d_offline (RunInterval)
!
!svn $Id: main3d_offline.F 1411 2011-05-02 23:02:13Z kate $
!=======================================================================
!  Copyright (c) 2002-2011 The ROMS/TOMS Group                         !
!    Licensed under a MIT/X style license                              !
!    See License_ROMS.txt                           Hernan G. Arango   !
!========================================== Alexander F. Shchepetkin ===
!                                                                      !
!  This subroutine is the main driver for nonlinear ROMS/TOMS when     !
!  configurated as a full 3D baroclinic ocean model.  It  advances     !
!  forward the primitive equations for all  nested  grids, if any,     !
!  for the specified time interval (seconds), RunInterval.             !
!  forward the primitive equations for a single time step.             !
!                                                                      !
!=======================================================================
!
      USE mod_param
      USE mod_parallel
# ifdef MODEL_COUPLING
      USE mod_coupler
# endif
      USE mod_iounits
      USE mod_scalars
      USE mod_stepping
!
# ifdef ANA_VMIX
      USE analytical_mod, ONLY : ana_vmix
# endif
# ifdef BIOLOGY
      USE biology_mod, ONLY : biology
# endif
# ifdef BBL_MODEL
      USE bbl_mod, ONLY : bblm
# endif
# ifdef BULK_FLUXES
#  ifdef CCSM_FLUXES
      USE ccsm_flux_mod, ONLY : ccsm_flux
#  else
      USE bulk_flux_mod, ONLY : bulk_flux
#  endif
# endif
# if defined ALBEDO || defined NCEP_FLUXES
      USE cawdir_eval_mod, ONLY : cawdir_eval
# endif
# if defined NCEP_FLUXES
      USE ncep_flux_mod, ONLY : ncep_flux
# endif
# ifdef BVF_MIXING
      USE bvf_mix_mod, ONLY : bvf_mix
# endif
      USE diag_mod, ONLY : diag
# ifdef TLM_CHECK
      USE dotproduct_mod, ONLY : nl_dotproduct
# endif
# ifdef GLS_MIXING
      USE gls_corstep_mod, ONLY : gls_corstep
      USE gls_prestep_mod, ONLY : gls_prestep
# endif
# if defined DIFF_3DCOEF || defined VISC_3DCOEF
      USE hmixing_mod, ONLY : hmixing
# endif
      USE ini_fields_mod, ONLY : ini_fields, ini_zeta
# ifdef LMD_MIXING
      USE lmd_vmix_mod, ONLY : lmd_vmix
# endif
# ifdef MY25_MIXING
      USE my25_corstep_mod, ONLY : my25_corstep
      USE my25_prestep_mod, ONLY : my25_prestep
# endif
# ifdef NESTING
      USE nesting_mod, ONLY : nesting
# endif
# ifdef AIR_OCEAN
      USE ocean_coupler_mod, ONLY : ocn2atm_coupling
# endif
# ifdef WAVES_OCEAN
      USE ocean_coupler_mod, ONLY : ocn2wav_coupling
# endif
      USE omega_mod, ONLY : omega
# ifdef NEARSHORE_MELLOR
      USE radiation_stress_mod, ONLY : radiation_stress
# endif
# ifndef TS_FIXED
      USE rho_eos_mod, ONLY : rho_eos
# endif
      USE rhs3d_mod, ONLY : rhs3d
# ifdef SEDIMENT
      USE sediment_mod, ONLY : sediment
# endif
# if defined AVERAGES && !defined ADJOINT
      USE set_avg_mod, ONLY : set_avg
# endif
# if defined AVERAGES2 && !defined ADJOINT
      USE set_avg2_mod, ONLY : set_avg2
# endif
# if defined ICE_MODEL && defined ICE_THERMO
      USE ice_frazil_mod, ONLY : ice_frazil
# endif
      USE set_massflux_mod, ONLY : set_massflux
# if defined SSH_TIDES || defined UV_TIDES || defined POT_TIDES
      USE set_tides_mod, ONLY : set_tides
# endif
      USE set_vbc_mod, ONLY : set_vbc
      USE set_zeta_mod, ONLY : set_zeta
      USE step2d_mod, ONLY : step2d
# ifndef TS_FIXED
      USE step3d_t_mod, ONLY : step3d_t
# endif
      USE step3d_uv_mod, ONLY : step3d_uv
# ifdef FLOATS
      USE step_floats_mod, ONLY : step_floats
# endif
      USE wvelocity_mod, ONLY : wvelocity
!
      implicit none
!
!  Imported variable declarations.
!
      real(r8), intent(in) :: RunInterval
!
!  Local variable declarations.
!
      integer :: ng
      integer :: my_iif, next_indx1, subs, tile, thread
# if defined FLOATS
      integer :: Lend, Lstr, chunk_size
# endif
      real(r8) :: my_StepTime
!
!=======================================================================
!  Time-step nonlinear 3D primitive equations by the specified time.
!=======================================================================
!
      my_StepTime=0.0_r8

      STEP_LOOP : DO WHILE (my_StepTime.le.RunInterval)

        my_StepTime=my_StepTime+MAXVAL(dt)
!
!  Set time indices and time clock.
!
        DO ng=1,Ngrids
          iic(ng)=iic(ng)+1
          nstp(ng)=1+MOD(iic(ng)-ntstart(ng),2)
          nnew(ng)=3-nstp(ng)
          nrhs(ng)=nstp(ng)
          time(ng)=time(ng)+dt(ng)
          tdays(ng)=time(ng)*sec2day
          CALL time_string (time(ng), time_code(ng))
        END DO
!
!-----------------------------------------------------------------------
!  Read in required data, if any, from input NetCDF files.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
          CALL get_data (ng)
          IF (exit_flag.ne.NoError) RETURN
        END DO
!
!-----------------------------------------------------------------------
!  If applicable, process input data: time interpolate between data
!  snapshots.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*thread,subs*(thread+1)-1,+1
              CALL set_data (ng, TILE)
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
        IF (exit_flag.ne.NoError) RETURN
!
!-----------------------------------------------------------------------
!  Initialize all time levels and compute other initial fields.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
          IF (iic(ng).eq.ntstart(ng)) THEN
!
!  Initialize free-surface and compute initial level thicknesses and
!  depths.
!
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(ng,numthreads)
            DO thread=0,numthreads-1
              subs=NtileX(ng)*NtileE(ng)/numthreads
              DO tile=subs*thread,subs*(thread+1)-1,+1
                CALL ini_zeta (ng, TILE, iNLM)
              END DO
            END DO
!$OMP END PARALLEL DO
!
!  Initialize other state variables.
!
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(ng,numthreads)
            DO thread=0,numthreads-1
              subs=NtileX(ng)*NtileE(ng)/numthreads
              DO tile=subs*(thread+1)-1,subs*thread,-1
                CALL ini_fields (ng, TILE, iNLM)
              END DO
            END DO
!$OMP END PARALLEL DO
          END IF
        END DO
!
!-----------------------------------------------------------------------
!  Compute horizontal mass fluxes (Hz*u/n and Hz*v/m), density related
!  quatities and report global diagnostics.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*thread,subs*(thread+1)-1,+1
              CALL set_massflux (ng, TILE)
# ifndef TS_FIXED
              CALL rho_eos (ng, TILE)
# endif
              CALL diag (ng, TILE)
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
        IF (exit_flag.ne.NoError) RETURN
# ifdef NESTING
        CALL nesting (5)
# endif

# ifndef OFFLINE_FLOATS
!-----------------------------------------------------------------------
!  Set fields for vertical boundary conditions. Process tidal forcing,
!  if any.
# if defined ADJUST_STFLUX || defined ADJUST_WSTRESS
!  Interpolate surface forcing increments and adjust surface forcing.
!  Load surface forcing into storage arrays.
# endif
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*thread,subs*(thread+1)-1,+1
# if defined NCEP_FLUXES || defined ALBEDO
              CALL cawdir_eval(ng, TILE)
# endif
# ifdef BULK_FLUXES
#  ifdef CCSM_FLUXES
              CALL ccsm_flux (ng, TILE)
#  else
              CALL bulk_flux (ng, TILE)
#  endif
# endif
# ifdef NCEP_FLUXES
              CALL ncep_flux(ng, TILE)
# endif
# ifdef BBL_MODEL
              CALL bblm (ng, TILE)
# endif
              CALL set_vbc (ng, TILE)
# if defined SSH_TIDES || defined UV_TIDES || defined POT_TIDES
              CALL set_tides (ng, TILE)
# endif
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
# ifdef NESTING
        CALL nesting (9)
# endif
!
!-----------------------------------------------------------------------
!  Run ice model for one step
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
#  if defined ICE_MODEL
          CALL seaice(ng)
#  endif
        END DO
# endif
!
!-----------------------------------------------------------------------
!  Compute time-dependent vertical/horizontal mixing coefficients for
!  momentum and tracers. Compute S-coordinate vertical velocity,
!  diagnostically from horizontal mass divergence.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile)                             &
!$OMP&            SHARED(nstp,numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*(thread+1)-1,subs*thread,-1
# ifndef OFFLINE_FLOATS
#  if defined ANA_VMIX
              CALL ana_vmix (ng, TILE, iNLM)
#  elif defined LMD_MIXING
              CALL lmd_vmix (ng, TILE)
#  elif defined BVF_MIXING
              CALL bvf_mix (ng, TILE)
#  endif
# endif
# if defined DIFF_3DCOEF || defined VISC_3DCOEF
              CALL hmixing (ng, TILE)
# endif
# if !defined OCLIMATOLOGY
              CALL omega (ng, TILE)
# endif
              CALL wvelocity (ng, TILE, nstp(ng))
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
# ifdef NESTING
        CALL nesting (10)
# endif
!
!-----------------------------------------------------------------------
!  Set free-surface to it time-averaged value.  If applicable,
!  accumulate time-averaged output data which needs a irreversible
!  loop in shared-memory jobs.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*thread,subs*(thread+1)-1,+1     ! irreversible loop
              CALL set_zeta (ng, TILE)
# ifdef DIAGNOSTICS
              CALL set_diags (ng, TILE)
# endif
# if defined AVERAGES && !defined ADJOINT
              CALL set_avg (ng, TILE)
# endif
# if defined AVERAGES2 && !defined ADJOINT
              CALL set_avg2 (ng, TILE)
# endif
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
# ifdef NESTING
        CALL nesting (11)
# endif
!
!-----------------------------------------------------------------------
!  If appropriate, write out fields into output NetCDF files.  Notice
!  that IO data is written in delayed and serial mode.  Exit if last
!  time step.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
          CALL output (ng)
          IF ((exit_flag.ne.NoError).or.                                &
     &        ((iic(ng).eq.(ntend(ng)+1)).and.(ng.eq.Ngrids))) RETURN 
        END DO
!
!-----------------------------------------------------------------------
!  Compute right-hand-side terms for 3D equations.
!-----------------------------------------------------------------------
!
# ifndef OFFLINE_FLOATS
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*(thread+1)-1,subs*thread,-1
              CALL rhs3d (ng, TILE)
# ifdef MY25_MIXING
              CALL my25_prestep (ng, TILE)
# elif defined GLS_MIXING
              CALL gls_prestep (ng, TILE)
# endif
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
# ifdef NESTING
        CALL nesting (12)
# endif
# endif

# ifndef OFFLINE_FLOATS
!
!-----------------------------------------------------------------------
!  Time-step vertical mixing turbulent equations and passive tracer
!  source and sink terms, if applicable.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(nnew,numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*thread,subs*(thread+1)-1,+1
              CALL omega (ng, TILE)
# ifdef MY25_MIXING
              CALL my25_corstep (ng, TILE)
# elif defined GLS_MIXING
              CALL gls_corstep (ng, TILE)
# endif
# ifdef BIOLOGY
              CALL biology (ng, TILE)
# endif
# ifdef SEDIMENT
              CALL sediment (ng, TILE)
# endif
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
# ifdef NESTING
        CALL nesting (17)
# endif
# endif

# ifndef TS_FIXED
!
!-----------------------------------------------------------------------
!  Time-step tracer equations.
!-----------------------------------------------------------------------
!
# if !defined OFFLINE_FLOATS
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
          DO thread=0,numthreads-1
            subs=NtileX(ng)*NtileE(ng)/numthreads
            DO tile=subs*(thread+1)-1,subs*thread,-1
              CALL step3d_t (ng, TILE)
#  if defined ICE_MODEL && defined ICE_THERMO
              CALL ice_frazil(ng, TILE)
#  endif
            END DO
          END DO
!$OMP END PARALLEL DO
        END DO
# ifdef NESTING
        CALL nesting (18)
# endif
# endif
# endif

# ifdef FLOATS
!
!-----------------------------------------------------------------------
!  Compute Lagrangian drifters trajectories.
!-----------------------------------------------------------------------
!
        DO ng=1,Ngrids
!$OMP PARALLEL DO PRIVATE(thread,chunk_size,Lstr,Lend)                  &
!$OMP&            SHARED(numthreads,Nfloats)
          DO thread=0,numthreads-1
            chunk_size=(Nfloats(ng)+numthreads-1)/numthreads
            Lstr=1+thread*chunk_size
            Lend=MIN(Nfloats(ng),Lstr+chunk_size-1)
            CALL step_floats (ng, Lstr, Lend)
          END DO
!$OMP END PARALLEL DO
# endif
# if defined FLOATS
!
!  Shift floats time indices.
!
          nfp1(ng)=MOD(nfp1(ng)+1,NFT+1)
          nf(ng)  =MOD(nf(ng)  +1,NFT+1)
          nfm1(ng)=MOD(nfm1(ng)+1,NFT+1)
          nfm2(ng)=MOD(nfm2(ng)+1,NFT+1)
          nfm3(ng)=MOD(nfm3(ng)+1,NFT+1)
        END DO
# endif
      END DO STEP_LOOP

      RETURN
      END SUBROUTINE main3d_offline
#else
      SUBROUTINE main3d_offline
      RETURN
      END SUBROUTINE main3d_offline
#endif
