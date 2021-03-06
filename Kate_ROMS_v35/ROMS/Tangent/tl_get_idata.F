#include "cppdefs.h"
#if defined TANGENT && defined TIMELESS_DATA
      SUBROUTINE tl_get_idata (ng)
!
!svn $Id: tl_get_idata.F 1411 2011-05-02 23:02:13Z kate $
!================================================== Hernan G. Arango ===
!  Copyright (c) 2002-2011 The ROMS/TOMS Group                         !
!    Licensed under a MIT/X style license                              !
!    See License_ROMS.txt                                              !
!=======================================================================
!                                                                      !
!  This routine reads input data that needs to be obtained only once.  !
!                                                                      !
!  Currently,  this routine is only executed in serial mode by the     !
!  main thread.                                                        !
!                                                                      !
!=======================================================================
!
      USE mod_param
      USE mod_grid
      USE mod_iounits
      USE mod_ncparam
      USE mod_parallel
      USE mod_scalars
# if defined UV_PSOURCE || defined TS_PSOURCE || defined Q_PSOURCE
      USE mod_sources
# endif
      USE mod_stepping
# if defined SSH_TIDES_NOT_YET || defined UV_TIDES_NOT_YET
      USE mod_tides
# endif

# if defined ANA_PSOURCE && \
    (defined UV_PSOURCE  || defined TS_PSOURCE || defined Q_PSOURCE)
!
      USE analytical_mod, ONLY : ana_psource
# endif
!
      implicit none
!
!  Imported variable declarations.
!
      integer, intent(in) :: ng
!
!  Local variable declarations.
!
      logical, dimension(3) :: update =                                 &
     &         (/ .FALSE., .FALSE., .FALSE. /)

      integer :: LBi, UBi, LBj, UBj
      integer :: itrc, is

# if defined ANA_PSOURCE && \
    (defined UV_PSOURCE  || defined TS_PSOURCE || defined Q_PSOURCE)
      integer :: subs, tile, thread
# endif

      real(r8) :: time_save = 0.0_r8
!
      SourceFile='tl_get_idata.F'
!
!  Lower and upper bounds for tiled arrays.
!
      LBi=LBOUND(GRID(ng)%h,DIM=1)
      UBi=UBOUND(GRID(ng)%h,DIM=1)
      LBj=LBOUND(GRID(ng)%h,DIM=2)
      UBj=UBOUND(GRID(ng)%h,DIM=2)

# ifdef PROFILE
!
!-----------------------------------------------------------------------
!  Turn on input data time wall clock.
!-----------------------------------------------------------------------
!
      CALL wclock_on (ng, iTLM, 3)
# endif

# if defined SSH_TIDES_NOT_YET || defined UV_TIDES_NOT_YET
!
!-----------------------------------------------------------------------
!  Tide period, amplitude, phase, and currents.
!-----------------------------------------------------------------------
!
!  Tidal Period.
!
      IF (iic(ng).eq.0) THEN
        CALL get_ngfld (ng, iTLM, idTper, ncFRCid(idTper,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  1, MTC, 1, 1, 1, NTC(ng), 1,                    &
     &                  TIDES(ng) % Tperiod(1))
        IF (exit_flag.ne.NoError) RETURN
      END IF
# endif

# ifdef SSH_TIDES_NOT_YET
!
!  Tidal elevation amplitude and phase. In order to read data as a
!  function of tidal period, we need to reset the model time variables
!  temporarily.
!
      IF (iic(ng).eq.0) THEN
        time_save=time(ng)
        time(ng)=8640000.0_r8
        tdays(ng)=time(ng)*sec2day

        CALL get_2dfld (ng, iTLM, idTzam, ncFRCid(idTzam,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  LBi, UBi, LBj, UBj, MTC, NTC(ng),               &
#  ifdef MASKING
     &                  GRID(ng) % rmask(LBi,LBj),                      &
#  endif
     &                  TIDES(ng) % SSH_Tamp(LBi,LBj,1))
        IF (exit_flag.ne.NoError) RETURN

        CALL get_2dfld (ng, iTLM, idTzph, ncFRCid(idTzph,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  LBi, UBi, LBj, UBj, MTC, NTC(ng),               &
#  ifdef MASKING
     &                  GRID(ng) % rmask(LBi,LBj),                      &
#  endif
     &                  TIDES(ng) % SSH_Tphase(LBi,LBj,1))
        IF (exit_flag.ne.NoError) RETURN

        time(ng)=time_save
        tdays(ng)=time(ng)*sec2day
      END IF
# endif

# ifdef UV_TIDES_NOT_YET
!
!  Tidal currents angle, phase, major and minor ellipse axis.
!
      IF (iic(ng).eq.0) THEN
        time_save=time(ng)
        time(ng)=8640000.0_r8
        tdays(ng)=time(ng)*sec2day

        CALL get_2dfld (ng, iTLM, idTvan, ncFRCid(idTvan,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  LBi, UBi, LBj, UBj, MTC, NTC(ng),               &
#  ifdef MASKING
     &                  GRID(ng) % rmask(LBi,LBj),                      &
#  endif
     &                  TIDES(ng) % UV_Tangle(LBi,LBj,1))
        IF (exit_flag.ne.NoError) RETURN


        CALL get_2dfld (ng, iTLM, idTvph, ncFRCid(idTvph,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  LBi, UBi, LBj, UBj, MTC, NTC(ng),               &
#  ifdef MASKING
     &                  GRID(ng) % rmask(LBi,LBj),                      &
#  endif
     &                  TIDES(ng) % UV_Tphase(LBi,LBj,1))
        IF (exit_flag.ne.NoError) RETURN

        CALL get_2dfld (ng, iTLM, idTvma, ncFRCid(idTvma,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  LBi, UBi, LBj, UBj, MTC, NTC(ng),               &
#  ifdef MASKING
     &                  GRID(ng) % rmask(LBi,LBj),                      &
#  endif
     &                  TIDES(ng) % UV_Tmajor(LBi,LBj,1))
        IF (exit_flag.ne.NoError) RETURN

        CALL get_2dfld (ng, iTLM, idTvmi, ncFRCid(idTvmi,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  LBi, UBi, LBj, UBj, MTC, NTC(ng),               &
#  ifdef MASKING
     &                  GRID(ng) % rmask(LBi,LBj),                      &
#  endif
     &                  TIDES(ng) % UV_Tminor(LBi,LBj,1))
        IF (exit_flag.ne.NoError) RETURN

        time(ng)=time_save
        tdays(ng)=time(ng)*sec2day
      END IF
# endif

# if defined UV_PSOURCE || defined TS_PSOURCE || defined Q_PSOURCE
!
!-----------------------------------------------------------------------
!  Point Sources/Sinks position, direction, special flag, and mass
!  transport nondimensional shape profile.  Point sources are at U-
!  and V-points.
#  ifdef ANA_PSOURCE
!
!  Since the point sources and sinks are specified with analytical
!  expressions, we need to get their positions to process internal
!  Land/Sea masking arrays during initialization.
#  endif
!-----------------------------------------------------------------------
!
      IF (iic(ng).eq.0) THEN

#  ifdef ANA_PSOURCE

!$OMP PARALLEL DO PRIVATE(thread,subs,tile) SHARED(numthreads)
        DO thread=0,numthreads-1
          subs=NtileX(ng)*NtileE(ng)/numthreads
          DO tile=subs*thread,subs*(thread+1)-1,+1
            CALL ana_psource (ng, TILE, iTLM)
          END DO
        END DO
!$OMP END PARALLEL DO

#  else

        CALL get_ngfld (ng, iTLM, idRxpo, ncFRCid(idRxpo,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  1, Nsrc(ng), 1, 1, 1, Nsrc(ng), 1,              &
     &                  SOURCES(ng) % Xsrc(1))
        IF (exit_flag.ne.NoError) RETURN

        CALL get_ngfld (ng, iTLM, idRepo, ncFRCid(idRepo,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  1, Nsrc(ng), 1, 1, 1, Nsrc(ng), 1,              &
     &                  SOURCES(ng) % Ysrc(1))
        IF (exit_flag.ne.NoError) RETURN

        CALL get_ngfld (ng, iTLM, idRdir, ncFRCid(idRdir,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  1, Nsrc(ng), 1, 1, 1, Nsrc(ng), 1,              &
     &                  SOURCES(ng) % Dsrc(1))
        IF (exit_flag.ne.NoError) RETURN

        CALL get_ngfld (ng, iTLM, idRvsh, ncFRCid(idRvsh,ng),           &
     &                  nFfiles(ng), FRC(1,ng), update(1),              &
     &                  1, Nsrc(ng), N(ng), 1, 1, Nsrc(ng), N(ng),      &
     &                  SOURCES(ng) % Qshape(1,1))
        IF (exit_flag.ne.NoError) RETURN

        DO is=1,Nsrc(ng)
          SOURCES(ng)%Isrc(is)=                                         &
     &                MAX(1,MIN(NINT(SOURCES(ng)%Xsrc(is)),Lm(ng)+1))
          SOURCES(ng)%Jsrc(is)=                                         &
     &                MAX(1,MIN(NINT(SOURCES(ng)%Ysrc(is)),Mm(ng)+1))
        END DO
#  endif
      END IF
# endif

# ifdef PROFILE
!
!-----------------------------------------------------------------------
!  Turn off input data time wall clock.
!-----------------------------------------------------------------------
!
      CALL wclock_off (ng, iTLM, 3)
# endif

      RETURN
      END SUBROUTINE tl_get_idata
#else
      SUBROUTINE tl_get_idata
      RETURN
      END SUBROUTINE tl_get_idata
#endif
