#include "cppdefs.h"
      MODULE radiation_stress_mod
#if defined NONLINEAR && defined NEARSHORE
!
!svn $Id: radiation_stress.F 1411 2011-05-02 23:02:13Z kate $
!=======================================================================
!  Copyright (c) 2002-2011 The ROMS/TOMS Group                         !
!    Licensed under a MIT/X style license                              !
!    See License_ROMS.txt                           Hernan G. Arango   !
!================================================== John C. Warner ====!
!                                                                      !
!  This routine computes the radiation stress contributions to the     !
!  momentum equations.                                                 !
!                                                                      !
!=======================================================================
!
      implicit none

      PRIVATE
      PUBLIC  :: radiation_stress

      CONTAINS

# if defined NEARSHORE_MELLOR05
#  include <nearshore_mellor05.h>
# elif defined NEARSHORE_MELLOR08
#  include <nearshore_mellor08.h>
# endif

#endif
      END MODULE radiation_stress_mod
