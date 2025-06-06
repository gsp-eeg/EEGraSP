r"""Graph Creation.
===================

Contains the functions used in EEGrasp to create Graphs 
"""

import numpy as np
from pygsp2 import graph_learning, graphs
from tqdm import tqdm

from .interpolate import interpolate_channel


def gaussian_kernel(x, sigma=0.1):
    """Gaussian Kernel Weighting function.

    Notes
    -----
    This function is supposed to be used in the PyGSP2 module but is
    repeated here since there is an error in the available version of the
    toolbox.

    References
    ----------
    * D. I. Shuman, S. K. Narang, P. Frossard, A. Ortega and
    P. Vandergheynst, "The emerging field of signal processing on graphs:
    Extending high-dimensional data analysis to networks and other
    irregular domains," in IEEE Signal Processing Magazine, vol. 30, no. 3,
    pp. 83-98, May 2013, doi: 10.1109/MSP.2012.2235192.
    
    """
    return np.exp(-np.power(x, 2.) / (2. * np.power(float(sigma), 2)))


def compute_graph(W=None, epsilon=.5, sigma=.1, distances=None, graph=None,
                  coordinates=None, method='enn', k=5):
    """Parameters
    ----------
    W : numpy ndarray | None
        If W is passed, then the graph is computed. Otherwise the graph
        will be computed with `self.W`. `W` should correspond to a
        non-sparse 2-D array. If None, the function will use the distance
        matrix computed in the instance of the class (`self.W`).
    epsilon : float
        Any distance greater than epsilon will be set to zero on the
        adjacency matrix.
    sigma : float
        Sigma parameter for the gaussian kernel.
    method : str, default="enn"
        Method to determine graph connectivity.
        - "enn": Use ε-neighbourhood with Gaussian kernel and distance thresholding.
        - "knn": Use K-Nearest Neighbors. Each node connects to its `k` nearest neighbors with Gaussian weighting.
    k : int, default=5
        Number of neighbors to connect when using method="knn".
        Ignored if method="epsilon".
        
    Returns
    -------
    G: PyGSP2 Graph object.
    """

    if W is None:
        if distances is None:
            raise TypeError(
                'No distances found. Distances have to be computed if W is not provided'
            )
        
        if method == "enn":
            graph_weights = gaussian_kernel(distances, sigma=sigma)
            graph_weights[distances > epsilon] = 0
            np.fill_diagonal(graph_weights, 0)

        elif method == "knn":
            from sklearn.neighbors import NearestNeighbors
            N = distances.shape[0]
            graph_weights = np.zeros_like(distances)
            nbrs = NearestNeighbors(n_neighbors=k+1).fit(distances)
            _, indices = nbrs.kneighbors(distances)
            for i in range(N):
                for j in indices[i][1:]:  # skip self
                    graph_weights[i, j] = gaussian_kernel(distances[i, j], sigma=sigma)

        else:
            raise ValueError(f"Unknown method '{method}'. Use 'enn' or 'knn'.")

        graph = graphs.Graph(graph_weights)

    else:
        graph_weights = W
        graph = graphs.Graph(W)

    if coordinates is not None:
        graph.set_coordinates(coordinates)

    return graph, graph_weights



def learn_graph(Z=None, a=0.1, b=0.1, gamma=0.04, maxiter=1000, w_max=np.inf,
                mode='Average', data=None, **kwargs):
    """Learn the graph based on smooth signals.

    Parameters
    ----------
    Z : ndarray
        Distance between the nodes. If not passed, the function will try to
        compute the euclidean distance using `self.data`. If `self.data` is
        a 2d array it will compute the euclidean distance between the
        channels. If the data is a 3d array it will compute a Z matrix per
        trial, assuming the first dimension in data is
        trials/epochs. Depending on the mode parameter, the function will
        average distance matrizes and learn the graph on the average
        distance or return a collection of adjacency matrices. Default is
        None.
    a : float
        Parameter for the graph learning algorithm, this controls the
        weights of the learned graph. Bigger a -> bigger weights in
        W. Default is 0.1.
    b : float
        Parameter for the graph learning algorithm, this controls the
        density of the learned graph. Bigger b -> more dense W. Default is
        0.1.
    mode : string
        Options are: 'Average', 'Trials'. If 'average', the function
        returns a single W and Z.  If 'Trials' the function returns a
        generator list of Ws and Zs. Default is 'Average'.
    data : ndarray | None
        2d array of channels by samples. If None, the function will use the
        data computed in the instance of the class (`self.data`).

    Returns
    -------
    W : ndarray
        Weighted adjacency matrix or matrices depending on mode parameter
        used. If run in 'Trials' mode then Z is a 3d array where the first
        dim corresponds to trials.
    Z : ndarray.
        Used distance matrix or matrices depending on mode parameter
        used. If run in 'Trials' mode then Z is a 3d array where the first
        dim corresponds to trials.
    """
    from .utils import euc_dist

    # If no distance matrix is given compute based on
    # data's euclidean distance
    # Check if data contains trials
    if data.ndim == 3:

        Zs = np.zeros((data.shape[0], data.shape[1], data.shape[1]))

        # Check if we want to return average or trials
        if mode == 'Trials':

            Ws = np.zeros((data.shape[0], data.shape[1], data.shape[1]))
            for i, d in enumerate(tqdm(data)):
                # Compute euclidean distance
                Z = euc_dist(d)

                W = graph_learning.graph_log_degree(Z, a, b, gamma=gamma, w_max=w_max,
                                                    maxiter=maxiter, **kwargs)
                W[W < 1e-5] = 0

                Ws[i, :, :] = W.copy()
                Zs[i, :, :] = Z.copy()

            return Ws, Zs

        elif mode == 'Average':

            for i, d in enumerate(tqdm(data)):
                # Compute euclidean distance
                Zs[i, :, :] = euc_dist(d)

            Z = np.mean(Zs, axis=0)
            W = graph_learning.graph_log_degree(Z, a, b, gamma=gamma, w_max=w_max,
                                                maxiter=maxiter, **kwargs)
            W[W < 1e-5] = 0

            return W, Z
    else:
        Z = euc_dist(data)

        W = graph_learning.graph_log_degree(Z, a, b, gamma=gamma, w_max=w_max,
                                            maxiter=maxiter, **kwargs)
        W = graph_learning.graph_log_degree(
            Z, a, b, gamma=gamma, w_max=w_max, maxiter=maxiter, **kwargs)
        W[W < 1e-5] = 0

        return W, Z


def fit_sigma(missing_idx: int | list[int] | tuple[int], data=None, distances=None,
              epsilon=0.5, min_sigma=0.1, max_sigma=1., step=0.1):
    """Find the best parameter for the gaussian kernel.

    Parameters
    ----------
    missing_idx : int | list | tuple
        Index of the missing channel.
    data : ndarray | None
        2d array of channels by samples. If None, the function will use the
        data computed in the instance of the class (`self.data`).
    distances : ndarray | None
        Distance matrix (2-dimensional array). It can be passed to the
        instance of the class or as an argument of the method. If None, the
        function will use the distance computed in the instance of the
        class (`self.distances`).
    epsilon : float
        Maximum distance to threshold the array. Default is 0.5.
    min_sigma : float
        Minimum value for the sigma parameter. Default is 0.1.
    max_sigma : float
        Maximum value for the sigma parameter. Default is 1.
    step : float
        Step for the sigma parameter. Default is 0.1.

    Notes
    -----
    Look for the best parameter of sigma for the gaussian kernel. This is
    done by interpolating a channel and comparing the interpolated data to
    the real data. After finding the parameter the graph is saved and
    computed in the instance class. The distance threshold is maintained.

    """
    # Create array of parameter values
    vsigma = np.arange(min_sigma, max_sigma, step=step)

    # Create time array
    time = np.arange(data.shape[1])

    # Mask to ignore missing channel
    ch_mask = np.ones(data.shape[0]).astype(bool)
    ch_mask[missing_idx] = False

    # Simulate eliminating the missing channel
    signal = data.copy()
    signal[missing_idx, :] = np.nan

    # Allocate array to reconstruct the signal
    all_reconstructed = np.zeros([len(vsigma), len(time)])

    # Allocate Error array
    error = np.zeros([len(vsigma)])

    # Loop to look for the best parameter
    for i, sigma in enumerate(tqdm(vsigma)):

        # Compute thresholded weight matrix
        graph, W = compute_graph(epsilon=epsilon, sigma=sigma, distances=distances)
        # Interpolate signal, iterating over time
        reconstructed = interpolate_channel(missing_idx=missing_idx, graph=graph,
                                            data=signal)

        all_reconstructed[i, :] = reconstructed[missing_idx, :]

        # Calculate error
        error[i] = np.linalg.norm(data[missing_idx, :] - all_reconstructed[i, :])

    # Eliminate invalid trials
    valid_idx = ~np.isnan(error)
    error = error[valid_idx]
    vsigma = vsigma[valid_idx]
    all_reconstructed = all_reconstructed[valid_idx, :]

    # Find best reconstruction
    best_idx = np.argmin(np.abs(error))
    best_sigma = vsigma[np.argmin(np.abs(error))]

    # Save best result in the signal array
    signal[missing_idx, :] = all_reconstructed[best_idx, :]

    # Compute the graph with the best result
    graph = compute_graph(distances, epsilon=epsilon, sigma=best_sigma)

    results = _return_results(error, signal, vsigma, 'sigma')

    return results


def fit_epsilon(missing_idx: int | list[int] | tuple[int], data=None, distances=None,
                sigma=0.1):
    """Find the best distance to use as threshold.

    Parameters
    ----------
    missing_idx : int
        Index of the missing channel. Not optional.
    data : ndarray | None
        2d array of channels by samples. If None, the function will use the
        data computed in the instance of the class (`self.data`). Default
        is `None`.
    distances : ndarray | None.
        Unthresholded distance matrix (2-dimensional array). It can be
        passed to the instance of the class or as an argument of the
        method. If None, the function will use the distance computed in the
        instance of the class (`self.distances`). Default is `None`.
    sigma : float
        Parameter of the Gaussian Kernel transformation. Default is 0.1.

    Returns
    -------
    results : dict
        Dictionary containing the error, signal, best_epsilon and epsilon
        values.

    Notes
    -----
    It will iterate through all the unique values of the distance matrix.
    data : 2-dimensional array. The first dim. is Channels
    and second is time. It can be passed to the instance class or the method
    """
    # Vectorize the distance matrix
    dist_tril = _vectorize_matrix(distances)

    # Sort and extract unique values
    vdistances = np.sort(np.unique(dist_tril))

    # Create time array
    time = np.arange(data.shape[1])

    # Mask to ignore missing channel
    ch_mask = np.ones(data.shape[0]).astype(bool)
    ch_mask[missing_idx] = False

    # Simulate eliminating the missing channel
    signal = data.copy()
    signal[missing_idx, :] = np.nan

    # Allocate array to reconstruct the signal
    all_reconstructed = np.zeros([len(vdistances), len(time)])

    # Allocate Error array
    error = np.zeros([len(vdistances)])

    # Loop to look for the best parameter
    for i, epsilon in enumerate(tqdm(vdistances)):

        # Compute thresholded weight matrix
        graph, W = compute_graph(distances, epsilon=epsilon, sigma=sigma)

        # Interpolate signal, iterating over time
        reconstructed = interpolate_channel(missing_idx=missing_idx, graph=graph,
                                            data=signal)
        all_reconstructed[i, :] = reconstructed[missing_idx, :]

        # Calculate error
        error[i] = np.linalg.norm(data[missing_idx, :] - all_reconstructed[i, :])

    # Eliminate invalid distances
    valid_idx = ~np.isnan(error)
    error = error[valid_idx]
    vdistances = vdistances[valid_idx]
    all_reconstructed = all_reconstructed[valid_idx, :]

    # Find best reconstruction
    best_idx = np.argmin(np.abs(error))
    best_epsilon = vdistances[np.argmin(np.abs(error))]

    # Save best result in the signal array
    signal[missing_idx, :] = all_reconstructed[best_idx, :]

    # Compute the graph with the best result
    graph, W = compute_graph(distances, epsilon=best_epsilon, sigma=sigma)

    results = _return_results(error, signal, vdistances, 'epsilon')
    return results


def _return_results(error, signal, vparameter, param_name):
    """Wrap results into a dictionary.

    Parameters
    ----------
    error : ndarray
        Errors corresponding to each tried parameter.
    vparameter : ndarray
        Values of the parameter used in the fit function.
    signal : ndarray
        Reconstructed signal.

    Notes
    -----
    In order to keep everything under the same structure this function
    should be used to return the results of any self.fit_* function.
    """
    best_idx = np.argmin(np.abs(error))
    best_param = vparameter[best_idx]

    results = {
        'error': error,
        'signal': signal,
        f'best_{param_name}': best_param,
        f'{param_name}': vparameter
    }

    return results


def _vectorize_matrix(mat):
    """Vectorize a symmetric matrix using the lower triangle.

    Returns
    -------
    mat : ndarray.
        lower triangle of mat
    """
    tril_indices = np.tril_indices(len(mat), -1)
    vec = mat[tril_indices]

    return vec
