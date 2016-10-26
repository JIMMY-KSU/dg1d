#================================================================================
#
# Imports
#
#================================================================================
import sys
import numpy as np
import constants

#================================================================================
#
# Function definitions
#
#================================================================================

#================================================================================
def max_wave_speed(u):
    """Returns the maximum wave speed for the Euler system"""

    # Primitive variables
    rho = u[0,0::3]
    v   = u[0,1::3]/rho
    E   = u[0,2::3]
    p   = (constants.gamma-1)*(E-0.5*rho*v*v)    

    # Get the wave speed
    wave_speed = np.fabs(v) + np.sqrt(constants.gamma*p/rho)

    return np.max(wave_speed)

#================================================================================
def riemann_rusanov(ul,ur):
    """Returns the Rusanov interface flux for the Euler equations

    V. V. Rusanov, Calculation of Interaction of Non-Steady Shock Waves with Obstacles, J. Comput. Math. Phys. USSR, 1, pp. 267-279, 1961.

    """

    # Initialize
    F = np.zeros(ul.shape)

    # Primitive variables and sound speeds
    rhoL = ul[0::3]
    vL   = ul[1::3]/rhoL
    EL   = ul[2::3]
    pL   = (constants.gamma-1)*(EL-0.5*rhoL*vL*vL)    
    aL   = np.sqrt(constants.gamma*pL/rhoL)

    rhoR = ur[0::3]
    vR   = ur[1::3]/rhoR
    ER   = ur[2::3]
    pR   = (constants.gamma-1)*(ER - 0.5*rhoR*vR*vR)
    aR   = np.sqrt(constants.gamma*pR/rhoR)

    # Find the maximum eigenvalue for each interface
    maxvap = np.maximum(np.fabs(vL)+aL,np.fabs(vR)+aR)

    # first: fx = rho*u
    F[0::3] = 0.5*(rhoL*vL + rhoR*vR - maxvap*(rhoR-rhoL))
    
    # second: fx = rho*u*u+p
    F[1::3] = 0.5*(rhoL*vL*vL+pL  + rhoR*vR*vR+pR - maxvap*(rhoR*vR-rhoL*vL))
    
    # third: fx = (E+p)*u
    F[2::3] = 0.5*((EL+pL)*vL + (ER+pR)*vR - maxvap*(ER-EL))

    return F


#================================================================================
def riemann_roe(ul,ur):
    """Returns the Roe interface flux for the Euler equations

    P. L. Roe, Approximate Riemann Solvers, Parameter Vectors and Difference Schemes, Journal of Computational Physics, 43, pp. 357-372.

    """

    # Initialize
    F = np.zeros(ul.shape)

    # Primitive variables and sound speeds
    rhoL = ul[0::3]
    vL   = ul[1::3]/rhoL
    EL   = ul[2::3]
    pL   = (constants.gamma-1)*(EL-0.5*rhoL*vL*vL)    
    aL   = np.sqrt(constants.gamma*pL/rhoL)
    HL   = (EL + pL)/rhoL
    
    rhoR = ur[0::3]
    vR   = ur[1::3]/rhoR
    ER   = ur[2::3]
    pR   = (constants.gamma-1)*(ER - 0.5*rhoR*vR*vR)
    aR   = np.sqrt(constants.gamma*pR/rhoR)
    HR   = (ER + pR)/rhoR
    
    # Compute Roe averages
    RT  = np.sqrt(rhoR/rhoL)
    rho = RT*rhoL
    v   = (vL+RT*vR)/(1+RT)
    H   = (HL+RT*HR)/(1+RT)
    a   = np.sqrt((constants.gamma-1)*(H-0.5*v*v))
    dp  = pR - pL

    # Roe waves strengths
    dV0 = (dp - rho*a*(vR-vL))/(2*a*a)
    dV1 = (rhoR-rhoL) - dp/(a*a)
    dV2 = (dp + rho*a*(vR-vL))/(2*a*a)
   
    # Absolute value of Roe eigenvalues
    ws0 = np.fabs(v-a)
    ws1 = np.fabs(v)
    ws2 = np.fabs(v+a)
   
    # Absolute value of Roe eigenvalues * Roe waves strengths
    ws0_dV0 = np.fabs(v-a) * (dp - rho*a*(vR-vL))/(2*a*a)
    ws1_dV1 = np.fabs(v)   * (rhoR-rhoL) - dp/(a*a)
    ws2_dV2 = np.fabs(v+a) * (dp + rho*a*(vR-vL))/(2*a*a)

    # Roe Right eigenvectors
    R00 = 1
    R01 = v-a
    R02 = H-v*a
    
    R10 = 1
    R11 = v
    R12 = 0.5*v*v

    R20 = 1
    R21 = v+a
    R22 = H+v*a

    # first: fx = rho*u
    F[0::3] = 0.5*(rhoL*vL + rhoR*vR) \
              -0.5*(ws0*dV0*R00+ 
                    ws1*dV1*R10+ 
                    ws2*dV2*R20)

    # second: fx = rho*u*u+p
    F[1::3] = 0.5*(rhoL*vL*vL+pL  + rhoR*vR*vR+pR) \
              -0.5*(ws0*dV0*R01+ 
                    ws1*dV1*R11+ 
                    ws2*dV2*R21)

    # third: fx = (E+p)*u
    F[2::3] =  0.5*((EL+pL)*vL + (ER+pR)*vR) \
               -0.5*(ws0*dV0*R02+  
                     ws1*dV1*R12+ 
                     ws2*dV2*R22)

    return F


#================================================================================
def interior_flux(ug):
    """Returns the interior flux for the Euler equations"""

    # Initialize
    F = np.zeros(ug.shape)

    # Primitive variables
    rho = ug[:,0::3]
    v   = ug[:,1::3]/rho
    E   = ug[:,2::3]
    p   = (constants.gamma-1)*(E-0.5*rho*v*v)    
    
    # Flux in x-direction
    F[:,0::3] = ug[:,1::3]
    F[:,1::3] = rho*v*v + p
    F[:,2::3] = (E+p)*v
    
    return F

#================================================================================
def sensing(sensors,thresholds,solution):
    """Two sensors to detect contact discontinuities and shocks for the
    Euler equations. See M. T. Henry de Frahan et al. JCP (2015).

    """

    # left/right solution
    ul = solution.u[0,:-solution.N_F]
    ur = solution.u[0,solution.N_F:]
    
    # physical variables on the left and right
    rhoL = ul[0::3]
    vL   = ul[1::3]/rhoL
    EL   = ul[2::3]
    pL   = (constants.gamma-1)*(EL-0.5*rhoL*vL*vL)    
    aL   = np.sqrt(constants.gamma*pL/rhoL)
    HL   = (EL + pL)/rhoL
    
    rhoR = ur[0::3]
    vR   = ur[1::3]/rhoR
    ER   = ur[2::3]
    pR   = (constants.gamma-1)*(ER - 0.5*rhoR*vR*vR)
    aR   = np.sqrt(constants.gamma*pR/rhoR)
    HR   = (ER + pR)/rhoR
    
    # Roe averages
    RT  = np.sqrt(rhoR/rhoL)
    v   = (vL+RT*vR)/(1+RT)
    H   = (HL+RT*HR)/(1+RT)
    a   = np.sqrt((constants.gamma-1)*(H-0.5*v*v))

    # contact wave strength
    drho = rhoR - rhoL
    dp   = pR - pL
    dV2  = drho - dp/(a*a)

    # Discontinuity sensor
    xsi = np.fabs(dV2)/(rhoL+rhoR)
    XSI = 2*xsi/((1+xsi)*(1+xsi))
    idx = np.array(np.where(XSI > thresholds[0]))
    sensors[idx] = 1
    sensors[idx+1] = 1

    # Shock sensor
    phi = np.fabs(dp) / (pL + pR)
    PHI = 2*phi/((1+phi)*(1+phi))
    idx = np.array(np.where( (PHI > thresholds[1]) & (vL-aL > v-a) & (v-a>vR-aR) ))
    sensors[idx] = 2
    sensors[idx+1] = 2