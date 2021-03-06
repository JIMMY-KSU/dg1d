# ========================================================================
#
# Imports
#
# ========================================================================
import numpy as np
from numpy.polynomial import Legendre as L   # import the Legendre class

import dg1d.basis as basis


# ========================================================================
#
# Class definitions
#
# ========================================================================
class Enhance:
    'Generate enhancement procedures'

    # ========================================================================
    def __init__(self, solution_order, method, solution_size):

        print("Generating the enhancement procedure.")

        # Parse the enhancement type
        method = method.split()
        self.etype = method[0]
        self.modes = [int(i) for i in method[1:]]
        # sort modes (makes the indexing cleaner in later functions)
        self.modes.sort()

        # enhancement order
        self.order = solution_order + len(self.modes)

        # The enhanced basis
        self.basis = basis.Basis(self.order)

        # Get the enhancement vectors
        A, Ainv, B, Binv = enhancement_matrices(solution_order, self.modes)
        self.alphaL, self.alphaR, self.betaL, self.betaR = left_enhancement_vectors(
            Ainv, Binv, solution_order, self.modes, self.basis.psi)

        # Pre-allocated storage of the face values
        self.uf_tmp = np.zeros((2, solution_size))

    # ========================================================================
    def face_value(self, u, N_F):
        """Calculates the value of the enhanced solution at the faces"""

        # Faces at j-1/2
        self.uf_tmp[0, N_F:] = np.dot(
            self.betaL, u[:, :-N_F]) + np.dot(self.betaR, u[:, N_F:])

        # Faces at j+1/2
        self.uf_tmp[
            1, :-N_F] = np.dot(self.alphaL, u[:, :-N_F]) + np.dot(self.alphaR, u[:, N_F:])

        return self.uf_tmp


# ========================================================================
def left_enhancement_vectors(Ainv, Binv, solution_order, modes, psi):
    """Returns the enhancement vectors

    These are the vectors that we apply to the solution (in the left
    and right cell) to get the value of the solution in the left cell
    at the interface between the left and right cell.

    See notes 2016/07/06 page 4 for more details.
    """

    # Multiply by the basis evaluated at the start and end points [-1,1]
    vs = np.dot(psi[0, :], Binv)
    ve = np.dot(psi[1, :], Ainv)

    # Split to get the vector acting on the left solution
    betaR = vs[:solution_order + 1]
    alphaL = ve[:solution_order + 1]

    # Split to get the vector acting on the right solution
    betaL = vs[solution_order + 1:]
    alphaR = ve[solution_order + 1:]
    # And add zeros for the modes of the right solution that we want
    # to leave out of the enhancement procedure
    for i in range(solution_order + 1):
        if i not in modes:
            betaL = np.insert(betaL, i, 0)
            alphaR = np.insert(alphaR, i, 0)

    return alphaL, alphaR, betaL, betaR


# ========================================================================
def enhancement_matrices(solution_order, modes):
    """Returns the enhancement matrices (and their inverse)

    Returns A and inv(A) where A \hat{u} = [uL;some_modes_of(uR)]
            B and inv(B) where B \hat{u} = [uR;some_modes_of(uL)]

    Note: this is slightly different than what I do in
    icb_functions.py (called by advection.py) where the right hand
    side contains the normalization factors (i.e A x = b where b =
    uL_i \int \phi_i \phi_i dx). Here I put \int \phi_i \phi_i dx into
    A and B (denoted norm down in the code below).

    """

    # Enhanced solution order
    order = solution_order + len(modes)

    # Submatrices to build the main matrix later
    a = np.diag(np.ones(solution_order + 1))
    b = np.zeros((solution_order + 1, len(modes)))
    cl = np.zeros((len(modes), order + 1))
    cr = np.zeros((len(modes), order + 1))

    # Loop on the modes we are keeping in the neighboring cell
    # (the right cell)
    for i, mode in enumerate(modes):

        # Loop on the enhancement basis
        for j in range(order + 1):

            # Basis function in the right cell
            l1 = L.basis(mode)

            # Enhanced basis function extending into the right cell (or left
            # cell)
            ll = basis.shift_legendre_polynomial(L.basis(j), 2)
            lr = basis.shift_legendre_polynomial(L.basis(j), -2)

            # Inner product for the left and right enhancements
            norm = basis.integrate_legendre_product(l1, l1)
            cl[i, j] = basis.integrate_legendre_product(l1, ll) / norm
            cr[i, j] = basis.integrate_legendre_product(l1, lr) / norm

    # Put the matrices together
    A = np.vstack((np.hstack((a, b)), cl))
    B = np.vstack((np.hstack((a, b)), cr))
    return A, np.linalg.inv(A), B, np.linalg.inv(B)
