cimport numpy as np
import numpy as np
from libc.math cimport log, sqrt, M_PI, exp, HUGE_VAL
cimport cython
from numpy.linalg import det, inv
from scipy.stats import multivariate_normal as mn

cdef double LOGSQRT2 = log(sqrt(2*M_PI))

cdef inline double log_add(double x, double y) nogil: return x+log(1.0+exp(y-x)) if x >= y else y+log(1.0+exp(x-y))

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef np.ndarray make_sym_matrix(int n, np.ndarray vals):
  m = np.zeros([n,n], dtype=np.double)
  xs,ys = np.triu_indices(n,k=1)
  m[xs,ys] = vals
  m[ys,xs] = vals
  m[ np.diag_indices(n) ] = 0 - np.sum(m, 0)
  return m

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef inline double _log_norm(np.ndarray x, np.ndarray x0, np.ndarray sigma, int n) nogil:
    diff = x-x0
    return -np.dot(diff.T, np.dot(inv(sigma), diff)) -n*0.5*LOGSQRT2 -0.5*log(det(sigma))


#solo un wrapper per python
def log_norm(np.ndarray x, np.ndarray x0, np.ndarray sigma):
    return mn(mean = x0, )
    #return _log_norm(x, x0, sigma, n)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef inline double _log_prob_component(np.ndarray mu, np.ndarray mean, np.ndarray sigma, double w) nogil:
    return log(w) + _log_norm(mu, mean, sigma)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef double _log_prob_mixture(np.ndarray mu, np.ndarray sigma, dict ev):
    cdef double logP = -HUGE_VAL
    cdef dict component
    for component in ev.values():
        logP = log_add(logP,_log_prob_component(mu, component['mean'], sigma, component['weight']))
    return logP

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef double _integrand(np.ndarray values, list events, double logN_cnst, int dim):
    cdef double logprob = 0.0
    cdef dict ev
    cdef np.ndarray mu = values[:dim]
    cdef np.ndarray sigma = make_sym_matrix(dim, values[dim:])
    for ev in events:
        logprob += _log_prob_mixture(mu, sigma, ev)
    return exp(logprob - logN_cnst)

def integrand(np.ndarray values, list events, double logN_cnst, int dim):
    return _integrand(values, events, logN_cnst, dim)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef double _compute_norm_const(np.ndarray mu, np.ndarray sigma, list events):
    cdef double logprob = 0.0
    cdef dict ev
    for ev in events:
        logprob += _log_prob_mixture(mu, sigma, ev)
    return logprob

def compute_norm_const(np.ndarray mu, np.ndarray sigma, list events):
    return _compute_norm_const(mu, sigma, events)
