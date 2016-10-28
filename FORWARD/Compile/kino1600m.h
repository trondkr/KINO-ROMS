/*
** svn $Id: kino1600m.h 172 2015-12-31 01:45:48Z arango $
*******************************************************************************
** Copyright (c) 2002-2007 The ROMS/TOMS Group                               **
**   Licensed under a MIT/X style license                                    **
**   See License_ROMS.txt                                                    **
*******************************************************************************
**
** Options for NS8KM
**
** Application flag:   NS8KM
** Input script:       ocean_ns8km.in
*/
#define NLM_DRIVER              /* Nonlinear Basic State trajectory */

/*
**-----------------------------------------------------------------------------
**  Nonlinear basic state tracjectory.
**-----------------------------------------------------------------------------
*/

#if defined NLM_DRIVER
#define UV_ADV
#define TS_C4VADVECTION
#define DJ_GRADPS
#define UV_COR
#define UV_QDRAG
#define UV_VIS2
#define MIX_S_UV
#define MIX_S_TS
#define TS_U3HADVECTION
#define SOLVE3D
#define TCLM_NUDGING
#define ANA_NUDGCOEF
#define SALINITY
#define NONLIN_EOS
#define CURVGRID
#define POWER_LAW
#define MASKING
#define AVERAGES
#define SOLAR_SOURCE
#undef SRELAXATION
#define MY25_MIXING
#define DEFLATE
#define CHARNOK /*Charnok Surface Roughness From Wind Stress */

#ifdef GLS_MIXING
# define KANTHA_CLAYSON
# undef  CANUTO_A
# undef K_C4ADVECTION
# define N2S2_HORAVG /*Horizontal Smoothing of Buoyancy/Shea */
#endif

#ifdef MY25_MIXING
# define N2S2_HORAVG
# define KANTHA_CLAYSON
#endif

#ifdef LMD_MIXING
# define N2S2_HORAVG /*Horizontal Smoothing of Buoyancy/Shea */
# define KANTHA_CLAYSON
# define  LMD_RIMIX       /* Add diffusivity due to shear instability */
# define  LMD_CONVEC      /* Add convective mixing due to shear instability */
# define  LMD_DDMIX       /* Add double-diffusive mixing */
#endif

#define ANA_BSFLUX
#define ANA_BTFLUX
#define ANA_SSFLUX
#define ANA_STFLUX
#define FORWARD_MIXING
#define FORWARD_WRITE
#endif


#undef VISC_GRID

/* ATMOSPHERIC FORCING */
#define BULK_FLUXES        /* turn ON or OFF bulk fluxes computation */
#ifdef BULK_FLUXES
# undef  ANA_RAIN          /* analytical rain fall rate */
# undef  ANA_PAIR          /* analytical surface air pressure */
# undef  ANA_HUMIDITY      /* analytical surface air humidity */
# undef  ANA_CLOUD         /* analytical cloud fraction */
# undef  ANA_TAIR          /* analytical surface air temperature */
# undef  ANA_WINDS         /* analytical surface winds */
# define EMINUSP           /* turn ON internal calculation of E-P */
# define ANA_SRFLUX        /* analytical surface shortwave radiation flux */
# define ALBEDO            /* use albedo equation for shortwave radiation */
# define CLOUDS
# undef  LONGWAVE_OUT      /* compute outgoing longwave radiation */
# define LONGWAVE          /* Compute net longwave radiation internally */
# define COOL_SKIN         /* turn ON or OFF cool skin correction *//* Ikke def hos Frode*/
# define SHORTWAVE
# define DIURNAL_SRFLUX
#endif

#define ATM_PRESS          /* use to impose atmospheric pressure onto sea surface */
#define SOLAR_SOURCE       /* define solar radiation source term */
#define SPECIFIC_HUMIDITY  /* if input is specific humidity in kg/kg */

/* TIDES */

#define KINOTIDES

#if defined KINOTIDES
#define SSH_TIDES          /* turn on computation of tidal elevation */
#define UV_TIDES           /* turn on computation of tidal currents */
#define ADD_FSOBC          /* Add tidal elevation to processed OBC data */
#define ADD_M2OBC          /* Add tidal currents  to processed OBC data */
#define RAMP_TIDES         /* Spin up tidal forcing */
#endif
#define WET_DRY

#define ICE_MODEL         /* Turn on ice model */ 

# ifdef ICE_MODEL
#  define ICE_THERMO
#    define ICE_MK
#    undef ICE_ALB_EC92
#  define ICE_MOMENTUM
#  define ICE_BULK_FLUXES
#    undef  ICE_MOM_BULK
#    define ICE_EVP
#  define ICE_ADVECT
#    define ICE_SMOLAR
#    define ICE_UPWIND
# endif

#define INLINE_2DIO
