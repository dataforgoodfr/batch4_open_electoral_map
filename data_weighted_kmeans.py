import pprint
import numpy as np
from matplotlib import pyplot
import random
import matplotlib.cm as cm
from haversine import haversine
import math


def show_kmeans(points, centers=None):
    #http://stackoverflow.com/questions/9401658/matplotlib-animating-a-scatter-plot
    xs = []
    ys = []
    c = []
    wts = []
    m = []
    colors = list(iter(cm.rainbow(np.linspace(0, 1, len(centers)))))
    for p in points:
        xs.append(p['coords'][0])
        ys.append(p['coords'][1])
        c.append(colors[p['c']])
        #wts.append(40+p['w'])
        wts.append(3)
        m.append('o')

    if centers:
        for i,cl in enumerate(centers):
            xs.append(cl['coords'][0])
            ys.append(cl['coords'][1])
            c.append('yellow')
            wts.append(500)
            m.append('*')

    for _s, _c, _x, _y,_sz in zip(m, c, xs, ys, wts):
        pyplot.scatter(_x, _y, marker=_s, c=_c, s=_sz, lw=0)

    pyplot.show()


def distance(lat1, long1, lat2, long2):
    return haversine((lat1, long1), (lat2, long2), miles=True)


def distance_try(lat1, long1, lat2, long2, weight):
    # return haversine((lat1, long1), (lat2, long2), miles=True) * (1 + 3.5 * weight)
    return haversine((lat1, long1), (lat2, long2)) / (weight)


def kmeans_evolution_weighted(points, centers, k, distance_method=distance_try, it_max=100, weight_step_scale=100, stop_criteria=1.05, DEBUG=False):
    """
    K-means clustering leading to similar-sized cluster.
    The point-cluster distances are weighted based on a
    per-cluster weight. The cluster weights evolve each iteration such that
    larger clusters loose weight (reducing the geographic range)
    and smaller ones gain weight (increasing the geographic range),
    leading to clusters of equal size. 

    The size of clusters is based on the sum of the point weights
    (for example population).

    parameters:
        k: number of clusters to produce

        Inputs:

        points: list of dictionaries
            with keys: 
                coords: np.array of real/integer values
                w: positive real

        centers: list of dictionaries
            with keys: 
                coords: np.array of real/integer values

        k: number of clusters

        it_max: max number of iterations

        distance_method:
            a method to calculat the distance between a point and the cluster.
            Takes two geolocations and the weight to scale by.

        weight_steo_scale: The scale of weight changes.
            The higher this value is the slower the step change is,
            and the more stable the iterations will be.

    """

    # number of dimensions
    d = len(points[0]['coords'])

    # Initialize the clusters
    for c in centers:
        c['n'] = 0      # number of member points
        c['pop'] = 0    # total population within the cluster
        c['w'] = 1      # weight to scale distances by

    total_population = 0
    # Assign each observation to the nearest cluster center.
    for p in points:
        distances = []
        for c in centers:
            distances.append(sum((p["coords"]-c["coords"])**2))
        idx = np.argmin(distances)
        p['c'] = idx
        centers[idx]["n"] += 1
        centers[idx]["pop"] += p['w'] # TODO: use notation 'pop' instead of 'w' for more clarity?
        total_population += p['w']

    # The population size that we want for the clusters
    goal_population = 200000
    #print("Goal Population: ", goal_population)

    # Initialize the clusters
    for j, c in enumerate(centers):
        c["coords"] = np.zeros(d)

    # Average the points in each cluster to get a new cluster center. 
    # (by location only)
    for p in points:
        centers[p['c']]["coords"] += p["coords"]

    for j, c in enumerate(centers):
                c["coords"] /= c["n"]
                continue

    it_num = 0

    distsq = np.zeros(k)
    while (it_num < it_max):

        # Print the clusters in debug mode
        if DEBUG:
            show_kmeans(points, centers)

        it_num += 1

        changes = 0
        for i, p in enumerate(points):
            ci = p['c']

            # Make sure not to have empty centers
            if centers[ci]['n'] <= 1:
                continue

            # For each cluster
            for cj, c in enumerate(centers):
                lat1 = p["coords"][1]
                long1 = p["coords"][0]
                lat2 = c["coords"][1]
                long2 = c["coords"][0]

                w = c["w"]

                if centers[cj]['n'] == 0:
                    # Make sure not to have empty centers
                    centers[cj]["coords"] = np.copy(p["coords"])
                    distsq[cj] = 0
                else:
                    distsq[cj] = distance_method(lat1, long1, lat2, long2, w)

            # Find the index of the minimum value of DISTSQ.
            nearest_cluster = np.argmin(distsq)

            # If that is not the cluster to which point I now belongs, move it there.
            if nearest_cluster == ci:
                continue

            cj = nearest_cluster
            centers[ci]['n'] -= 1
            centers[cj]['n'] += 1

            # assign the point its new home
            p['c'] = cj

            # indicate that a cluster was modified on this iteration
            changes += 1

        ## Recompute cluster centers after each iteration
        # TODO: this part could probably be more efficient by directly calculating 
        #       changes in the update cluster code above
        for j, c in enumerate(centers):
            c["coords"] = np.zeros(d)
            c['n'] = 0
            c['pop'] = 0

        for p in points:
            centers[p['c']]["coords"] += p["coords"]
            centers[p['c']]["n"] += 1
            centers[p['c']]["pop"] += p['w']

        pops = []

        for j, c in enumerate(centers):
            c["coords"] /= c["n"]
            # c["w"] = c["pop"] / goal_population

            weight_delta = (goal_population - c["pop"]) / goal_population
            c["w"] *= 1 + (weight_delta / weight_step_scale)

            if weight_delta != 1:
                changes += 1
            # print("id:"+str(j), c["pop"], round(weight_delta,4), round(c["w"], 4))

            pops.append(c["pop"])

        max_pop = max(pops)
        min_pop = min(pops)
        
        # if it_num % 100 == 0: 
        #print(max_pop/min_pop)

        if min_pop != 0:
            #print(max_pop, min_pop)
            #print(round(max_pop/min_pop, 4))

            # Exit if the ration is under the stopping criteria
            if max_pop/min_pop <= stop_criteria:
                break

        # Exit if no reassignments were made during this iteration.
        if changes == 0:
            break

    #print("DONE")
    #print("Iterations: ", it_num)
    #print.pprint(centers)
    #print("RATIO : ", min_pop, max_pop, round(max_pop/min_pop, 4))
    #print("POPS: ", pops)

    return [points, centers, it_num]




def data_weighted_kmeans(points, centers, k, it_max=100):
    '''
        Implements weighted k-means where individual data points are weighted

        Code was ported from matlab code:
            http://people.sc.fsu.edu/~jburkardt/m_src/kmeans/kmeans.html

            specifically http://people.sc.fsu.edu/~jburkardt/m_src/kmeans/kmeans_w_03.m

        A natural extension of the K-Means problem allows us to include some more information, namely, 
        a set of weights associated with the data points. These might represent a measure of importance, 
        a frequency count, or some other information. The intent is that a point with a weight of 5.0 is 
        twice as "important" as a point with a weight of 2.5, for instance. This gives rise to the 
        "weighted" K-Means problem.

        In the weighted K-Means problem, we are given a set of N points X(I) in M-dimensions, and a 
        corresponding set of nonnegative weights W(I). The goal is to arrange the points into K clusters, 
        with each cluster having a representative point Z(J), usually chosen as the weighted centroid of 
        the points in the cluster:

        Z(J) = Sum ( all X(I) in cluster J ) W(I) * X(I) / Sum ( all X(I) in cluster J ) W(I).

        The weighted energy of cluster J is
            E(J) = Sum ( all X(I) in cluster J ) W(I) * || X(I) - Z(J) ||^2

        Inputs:

        points: list of dictionaries
            with keys: 
                coords: np.array of real/integer values
                w: positive real

        centers: list of dictionaries
            with keys: 
                coords: np.array of real/integer values

        k: number of clusters

        it_max: max number of iterations

    '''
    # number of dimensions
    d = len(points[0]['coords'])

    for c in centers:
        c['n'] = 0
        c['w'] = 0

    # Assign each observation to the nearest cluster center.
    for p in points:
        distances = []
        for c in centers:
            distances.append(sum((p["coords"]-c["coords"])**2))
        idx = np.argmin(distances)
        p['c'] = idx
        centers[idx]["n"] += 1
        centers[idx]["w"] += p['w']

    for j, c in enumerate(centers):
        c["coords"] = np.zeros(d)

    # Average the points in each cluster to get a new cluster center.
    for p in points:
        centers[p['c']]["coords"] += p["coords"] * p['w']
    for c in centers:
        c["coords"] /= c['w']

    it_num = 0
    distsq = np.zeros(k)
    while (it_num < it_max):
        it_num += 1
        swap = 0
        for i, p in enumerate(points):
            ci = p['c']

            if centers[ci]['n'] <= 1:
                continue

            for cj, c in enumerate(centers):
                lat1 = p["coords"][1]
                long1 = p["coords"][0]
                lat2 = c["coords"][1]
                long2 = c["coords"][0]
                if ci == cj:
                    distsq[cj] = ((distance(lat1, long1, lat2, long2)**2) * c['w']) / (c['w'] - p['w'])
                elif centers[cj]['n'] == 0:
                    centers[cj]["coords"] = np.copy(p["coords"])
                    distsq[cj] = 0
                else:
                    distsq[cj] = ((distance(lat1, long1, lat2, long2)**2) * c['w']) / (c['w'] + p['w'])

            # Find the index of the minimum value of DISTSQ.
            nearest_cluster = np.argmin(distsq)

            # If that is not the cluster to which point I now belongs, move it there.
            if nearest_cluster == ci:
                continue

            cj = nearest_cluster
            centers[ci]["coords"] = (centers[ci]['w'] * centers[ci]["coords"] - p['w'] * p["coords"]) / (centers[ci]['w'] - p['w'])
            centers[cj]["coords"] = (centers[cj]['w'] * centers[cj]["coords"] + p['w'] * p["coords"]) / (centers[cj]['w'] + p['w'])
            centers[ci]['n'] -= 1
            centers[cj]['n'] += 1
            centers[ci]['w'] -= p['w']
            centers[cj]['w'] += p['w']

            # assign the point its new home
            p['c'] = cj

            swap += 1
        # Exit if no reassignments were made during this iteration.
        if swap == 0:
            break
    return [points, centers, it_num]



def data_nonweighted_kmeans(points, centers, k, distance_method=distance_try, it_max=100, weight_step_scale=100):
    # number of dimensions
    d = len(points[0]['coords'])

    for c in centers:
        c['n'] = 0
        c['pop'] = 0
        c['w'] = 1

    total_population = 0
    # Assign each observation to the nearest cluster center.
    for p in points:
        distances = []
        for c in centers:
            distances.append(sum((p["coords"]-c["coords"])**2))
        idx = np.argmin(distances)
        p['c'] = idx
        centers[idx]["n"] += 1
        centers[idx]["pop"] += p['w']
        total_population += p['w']
    
    goal_population = total_population / k
    #print("goal_population", goal_population)

    for j, c in enumerate(centers):
        c["coords"] = np.zeros(d)

    # Average the points in each cluster to get a new cluster center. 
    # (by location only)
    for p in points:
        centers[p['c']]["coords"] += p["coords"]

    for j, c in enumerate(centers):
        c["coords"] /= c["n"]
        # c["w"] = 1 + (c["pop"] - goal_population) / goal_population
        # print(c["pop"], c["w"])

    #pprint.pprint(centers)
    it_num = 0
    # return [points, centers, it_num]

    distsq = np.zeros(k)
    while (it_num < it_max):
        # print("ITERATION")
        # show_kmeans(points, centers)
        it_num += 1
        changes = 0
        for i, p in enumerate(points):
            ci = p['c']

            # Make sure not to have empty centers
            if centers[ci]['n'] <= 1:
                continue

            for cj, c in enumerate(centers):
                lat1 = p["coords"][1]
                long1 = p["coords"][0]
                lat2 = c["coords"][1]
                long2 = c["coords"][0]

                w = c["w"]

                if centers[cj]['n'] == 0:
                    # Make sure not to have empty centers
                    centers[cj]["coords"] = np.copy(p["coords"])
                    distsq[cj] = 0
                else:
                    #print("dist: ", distance_method(lat1, long1, lat2, long2, w), lat1, long1, lat2, long2, w)
                    distsq[cj] = distance_method(lat1, long1, lat2, long2, w)

            #print(p["coords"])
            #if i == 0:
            #    print(distsq)
            
            # Find the index of the minimum value of DISTSQ.
            nearest_cluster = np.argmin(distsq)

            # If that is not the cluster to which point I now belongs, move it there.
            if nearest_cluster == ci:
                continue


            cj = nearest_cluster
            centers[ci]['n'] -= 1
            centers[cj]['n'] += 1

            cj = nearest_cluster

            # assign the point its new home
            p['c'] = cj

            changes += 1
        
        ## RECOMPUTE CENTER POINTS
        
        # RESET
        for j, c in enumerate(centers):
            c["coords"] = np.zeros(d)
            c['n'] = 0
            c['pop'] = 0
            # c['w'] = 0

        
        for p in points:
            centers[p['c']]["coords"] += p["coords"]
            centers[p['c']]["n"] += 1
            centers[p['c']]["pop"] += p['w']

        max_pop = 0
        min_pop = total_population
        pops = []
        
        for j, c in enumerate(centers):
            c["coords"] /= c["n"]
            # c["w"] = c["pop"] / goal_population

            weight_delta = (goal_population - c["pop"]) / goal_population
            c["w"] *= 1 + (weight_delta / weight_step_scale)

            if weight_delta != 1:
                changes += 1
            # print("id:"+str(j), c["pop"], round(weight_delta,4), round(c["w"], 4))

            max_pop = max(max_pop, c["pop"])
            min_pop = min(min_pop, c["pop"])
            pops.append(c["pop"])
            
        if min_pop != 0:
           #print(max_pop, min_pop)
            #print(round(max_pop/min_pop, 4))
            if max_pop/min_pop < 1.05:
                break
        #pprint.pprint(centers)

        # Exit if no reassignments were made during this iteration.
        if changes == 0:
            break
    
    #print("DONE")
    #print("Iterations: ", it_num)
    #pprint.pprint(centers)
    
    #print("RATIO : " , min_pop, max_pop, round(max_pop/min_pop, 4))
    #print("POPS: ", pops)

    return [points, centers, it_num]


def randomize_initial_cluster(points,k,seed=None):
    '''
        randomly select k starting points
    '''
    if seed:
        random.seed(seed)
    indices = list(range(0,len(points)))
    random.shuffle(indices)
    centers = []
    for i in indices[:k]:
        centers.append({"coords": np.copy(points[i]['coords'])})
    return centers


def equally_spaced_initial_clusters(points, k):
    '''
    set them equally spaced across x
    '''
    xs = []
    ys = []
    for p in points:
        xs.append(p['coords'][0])
        ys.append(p['coords'][1])
    xs = np.array(xs)
    meany = np.mean(np.array(ys))
    minx = np.min(xs)
    maxx = np.max(xs)
    if k == 1:
        return [{"coords": np.array([np.mean(np.array(xs)), meany])}]
    step = (maxx-minx) / (k-1)
    centers = []
    [centers.append({"coords": np.array([minx + i * step, meany])}) for i in range(k)]
    return centers
