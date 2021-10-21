import numpy as np
import os
import h5py

h = 0.674
om = 0.3089
ol = 0.6911

def LumDist(z, om, ol, h):
    return 3e3*(z + (1-om +ol)*z**2/2.)/h

def dLumDist(z, om, ol, h):
    return 3e3*(1+(1-om+ol)*z)/h

def RedshiftCalculation(LD, om, ol, h, zinit=0.3, limit = 0.001):
    '''
    Redshift given a certain luminosity, calculated by recursion.
    Limit is the less significative digit.
    '''
    LD_test = LumDist(zinit, om, ol, h)
    if abs(LD-LD_test) < limit :
        return zinit
    znew = zinit - (LD_test - LD)/dLumDist(zinit,om, ol, h)
    return RedshiftCalculation(LD, om, ol, h, zinit = znew)

def load_data(path, seed = False, par = 'm1', n_samples = -1, h = 0.674, om = 0.315, ol = 0.685):
    '''
    Loads the data from .txt files (for simulations) or .h5/.hdf5 files (posteriors from GWTC).
    Default cosmological parameters from Planck Collaboration (2021) in a flat Universe (https://www.aanda.org/articles/aa/pdf/2020/09/aa33910-18.pdf)
    
    Arguments:
        :str path:      folder with data files
        :bool seed:     fixes the seed to a default value (1) for reproducibility
        :str par:       parameter to extract from GW posteriors (m1, m2, mc, z, chi_effective)
        :int n_samples: number of samples for (random) downsampling. Default -1: all samples
        :double h:      Hubble constant H0/100 [km/(s*Mpc)]
        :double om:     matter density parameter
        :double ol:     cosmological constant density parameter
    
    Returns:
        :np.ndarray:    samples
        :np.ndarray:    names
    '''
    if seed:
        np.random.seed(seed = 1)
    event_files = [path+'/'+f for f in os.listdir(path) if not f.startswith('.')]
    events = []
    names  = []
    for event in event_files:
        name, ext = event.split('/')[-1].split('.')
        names.append(name)
        if ext == 'txt':
            if n_samples > -1:
                samples = np.genfromtxt(event)
                s = int(min([n_samples, len(samples)]))
                events.append(np.random.choice(samples, size = s, replace = False))
            else:
                events.append(np.sort(np.genfromtxt(event)))
        else:
            events.append(np.sort(unpack_gw_posterior(event, par = par, n_samples = n_samples)))
    return (np.array(events), np.array(names))

def unpack_gw_posterior(event, par, n_samples = -1):
    '''
    Reads data from .h5/.hdf5 GW posterior files.
    Implemented 'm1', 'm2', 'mc', 'z', 'chi_eff'.
    
    Arguments:
        :str event:     file to read
        :str par:       parameter to extract
        :int n_samples: number of samples for (random) downsampling. Default -1: all samples
    
    Returns:
        :np.ndarray:    samples
    '''
    
    with h5py.File(data_folder + file, 'r') as f:
        print(file)
        try:
            data = f['PublicationSamples']['posterior_samples']
            if par == 'm1':
                samples = data['mass_1_source']
            if par == 'm2':
                samples = data['mass_2_source']
            if par == 'mc':
                samples = data['chirp_mass']
            if par == 'z':
                samples = data['redshift']
            if par == 'chi_eff':
                samples = data['chi_eff']
            if n_samples > -1:
                s = int(min([n_samples, len(samples)]))
                return np.random.choice(samples, size = s, replace = False)
            else:
                return samples
        except:
            data = f['Overall_posterior']
            LD        = data['luminosity_distance_Mpc']
            z         = np.array([RedshiftCalculation(l, om, ol, h) for l in LD])
            m1_detect = data['m1_detector_frame_Msun']
            m2_detect = data['m2_detector_frame_Msun']
            m1        = m1_detect/(1+z)
            m2        = m2_detect/(1+z)
            
            if par == 'z':
                samples = z
            if par == 'm1':
                samples = m1
            if par == 'm2':
                samples = m2
            if par == 'mc':
                samples = (m1*m2)**(3./5.)/(m1+m2)**(1./5.)
            if par == 'chi_eff':
                s1   = data['spin1']
                s2   = data['spin2']
                cos1 = data['costilt1']
                cos2 = data['costilt2']
                q    = m2/m1
                samples = (s1*cos1 + q*s2*cos2)/(1+q)
            
            if n_samples > -1:
                s = int(min([n_samples, len(samples)]))
                return np.random.choice(samples, size = s, replace = False)
            else:
                return samples