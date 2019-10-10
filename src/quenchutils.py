"""quenchutils.py

Various useful utilities for analysis of quantum quench data
"""

import numpy as np
from numpy import pi as π
from scipy.integrate import quad

# ---------------------------------------------------------------------------------------
def get_ED_fname(N,Vi,Vf,Δt,ti,tf,n,data_dir,fmt='partEE'):
    '''data file names''' 
    return data_dir + fmt + '_{:02d}_{:02d}_{:+5.3f}_{:+5.3f}_{:6.4f}_{:06.3f}_{:06.3f}_{:1d}.dat'.format(2*N,N,Vi,Vf,Δt,ti,tf,n)

# ---------------------------------------------------------------------------------------
def lookup(N,Vi,Vf,Δt,n, bc='PBC'):
    '''key for data dictionary'''
    return u'N={:02d}, Vi={:+5.3f}, Vf={:+5.3f}, Δt={:6.4f}, n={:1d} {:s}'.format(N,Vi,Vf,Δt,n,bc)

# ---------------------------------------------------------------------------------------
def vkey(V):
    return 'V={:5.3f}'.format(V)

# ---------------------------------------------------------------------------------------
def γeq(K):
    '''Equilbrium LL exponent  
    '''
    return np.sqrt((K+1/K-2)/2)

# ---------------------------------------------------------------------------------------
def γ(K):
    '''Post quench Luttinger exponent.  
       see: https://link.aps.org/doi/10.1103/PhysRevA.80.063619 page 6, left column
    '''
    return 0.5*np.abs(K - 1.0/K)
# ---------------------------------------------------------------------------------------
def KV(V):
    '''Luttiger parameter  obtained from Bethe Ansatz of J-V model.
       see: http://link.aps.org/doi/10.1103/PhysRevLett.45.1358
       We take J = 1 here.
    '''
    return π/(2*np.arccos(-V/2))

# ---------------------------------------------------------------------------------------
def vV(V):
    '''Luttiger velocity (in units of J*latice spacing) obtained from Bethe Ansatz of J-V model.
       We take J = 1 here.
    '''
    return (1.0/(1 - np.arccos(-V/2)/π)) * np.sin(π*(1 - np.arccos(-V/2)/π))

# ---------------------------------------------------------------------------------------
def tscalefactor(V):
    '''Rescaling factor of ED times to compare with Luttinger liquid data.
    '''
    return π * np.sqrt(1-(V/2)**2) / (np.arccos(V/2))

#-----------------------------------------------------------------------------------
from mpmath import hyper
from mpmath import gamma as Γ

def _f(q,γ,ϵ):
    ''' The distribution function. Checked with Mathematica on 2018-06-20
    '''
    
    a1 = [1/2]
    b1 = [3/2,3/2-γ**2/2]
    a2 = [γ**2/2]
    b2 = [γ**2/2 + 1/2,γ**2/2+1]
    zm = π*ϵ - q
    zp = π*ϵ + q
    
    p1 = Γ((γ**2-1)/2)/(2*np.sqrt(π)*Γ(γ**2/2))
    p2 = Γ(-γ**2)*np.sin(π*γ**2 / 2) / π
    
    t1 = p1*(zm*hyper(a1,b1,zm**2/4) + zp*hyper(a1,b1,zp**2/4))
    t2 = p2*(np.sign(zm)*(np.abs(zm)**(γ**2))*hyper(a2,b2,zm**2/4) + zp**(γ**2) * hyper(a2,b2,zp**2/4))
    
    cf = np.float(t1-t2)
    if cf > 1.0E-16:
        return np.float(t1-t2)
    else:
        return 0.0

f = np.vectorize(_f)
#------------------------------------------------------------------------------
def k_Fermi(L):
    if int(L/2) % 2:
        return π/2
    else:
        return π/2 + π/L
    
#------------------------------------------------------------------------------
def _kernelf(x,n,L,γ,ϵ):
    '''Kernel for the above integral
    '''
    if np.abs(x) < 1.0E-12:
        return 0.5
    
    t1 = np.cos(2*π*n*x/L)
    t2 = np.sin(k_Fermi(L)*x)/np.sin(π*x/L)
    t3 = np.abs(np.sin((π/L)*(x+complex(0,2)*ϵ)))**(γ**2)
    return (π*np.sinh(2*π*ϵ/L)**(γ**2)/(2*k_Fermi(L)*L)) * t1 * t2 / t3

kernelf = np.vectorize(_kernelf)

#------------------------------------------------------------------------------
def _fL(n,L,γ,ϵ):
    ''' finite size distribution function'''
    if int(L/2) % 2:
        norm = 1.0
    else:
        norm = 1.0 + 2.0/L
    return norm*quad(kernelf, -0.5*L, 0.5*L, args=(n,L,γ,ϵ))[0]
fL = np.vectorize(_fL)

#------------------------------------------------------------------------------
# infinite LL
def Nρlogρ(q,γ,ϵ):
    '''N ρ(n=1) log ρ(n=1)
    '''
    return -f(q,γ,ϵ) * np.log(np.abs(f(q,γ,ϵ))) / (π*ϵ) 

#------------------------------------------------------------------------------
def _A1_eq(γ,ϵ,Λ=10):
    ''' -Tr ρ(n=1) log ρ(n=1)'''
    return quad(Nρlogρ, 0.0, π*ϵ + Λ, args=(γ,ϵ))[0]
A1_eq = np.vectorize(_A1_eq)

#------------------------------------------------------------------------------
# finite LL
def _A1L_eq(L,γ,ϵ):
    ''' -Tr ρ(n=1|L) log ρ(n=1|L)'''
    return (-4/L)*np.sum([fL(n,L,γ,ϵ)*np.log(fL(n,L,γ,ϵ)) for n in range(1,2*L)])
A1L_eq = np.vectorize(_A1L_eq)

#------------------------------------------------------------------------------
def Sb(ϵ,γ):
    '''The boson entropy.'''
    Q = 2 + γ**2 - 2*np.sqrt(1+γ**2)
    t1 = (2 - np.log(2))*np.log(2)
    t2 = (np.log(2) - 1 - np.sqrt(1+γ**2))*np.log(γ**2)
    t3 = np.log(Q)*(np.sqrt(1+γ**2) + 0.25*np.log(Q/γ**4))
    return -(t1+t2+t3)/(π*ϵ)

#------------------------------------------------------------------------------
def Sb1(ϵ,γ):
    '''inconsistent simple regulator'''
    n0 = γ**2/2
    return -(n0*np.log(n0) - (1+n0)*np.log(1+n0))/(π*ϵ)

#------------------------------------------------------------------------------
def Sbn(n0,ϵ):
    '''inconsistent simple regulator'''
    return -(n0*np.log(n0) - (1+n0)*np.log(1+n0))/(π*ϵ)

#------------------------------------------------------------------------------
def get_asymptotic_value(t,EE,N,Vf,Δt):
    
    # get the index where we start the average
    idx = np.where(np.abs(t*tscalefactor(Vf)-0.5*N)<Δt*tscalefactor(Vf))[0][0]
    
    # find out how many data points we have in total to average
    num_times = len(t)
    
    # break into M pieces
    M = 4
    width = int(num_times/M)
    norm = 2/cN
    asymp = []
    for i in range(M):
        start = idx + width*i
        end = start + width
        if i == M-1:
            end = len(t)
        asymp.append(np.average(EE[start:end])*norm)
    
    asymp = np.array(asymp)
    
    return np.average(asymp),np.std(asymp)/np.sqrt(M)

#------------------------------------------------------------------------------
def get_binned_error(data):
    '''Get the standard error in mc_data and return neighbor averaged data.'''
    N_bins = data.shape[0]
    Δ = np.std(data,axis=0)/np.sqrt(N_bins)
    
    start_bin = N_bins % 2
    binned_data = 0.5*(data[start_bin::2]+data[start_bin+1::2])
    
    return Δ,binned_data

#------------------------------------------------------------------------------
def binning_error(data):
    '''Perform a binning analysis'''
    
    from scipy.signal import find_peaks
    
    # number of possible binning levels
    num_levels = np.int(np.log2(data.shape[0]/4))+1

    # compute the error at each bin level
    Δ = []
    num_bins = []
    binned_data = data
    
    for n in range(num_levels):
        Δₙ,binned_data = get_binned_error(binned_data)
        Δ.append(Δₙ)
        num_bins.append(2**n) 
        
    Δ = np.array(Δ)
    
    # find the maxima which corresponds to the error
    if Δ.ndim == 1:
        plateau = find_peaks(Δ)[0]
        if plateau.size > 0:
            binned_error = Δ[plateau[0]]
        else:
            binned_error = np.max(Δ)
            print('Binning Converge Error: no plateau found')
    else:
        num_est = Δ.shape[1]
        binned_error = np.zeros(num_est)
        
        for iest in range(num_est):
            plateau = find_peaks(Δ[:,iest])[0]
            if plateau.size > 0:
                binned_error[iest] = Δ[plateau[0],iest]
        else:
            binned_error[iest] = np.max(Δ[:,iest])
            print('Binning Converge Error: no plateau found')
            
    return np.array(num_bins),Δ,binned_error