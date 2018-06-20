#Imports
import geopandas as gpd
import numpy as np
import pandas as pd

#k-means
import data_weighted_kmeans
import importlib

#graph
import folium
import random

#widget
import ipywidgets as widgets
import os
import time
import selenium
from selenium import webdriver


class CirconscriptionBuilder():
    def load(self):
        # Load data
        print("Load shapefile...")
        self.iris = gpd.read_file("data/CONTOURS-IRIS_2-1__SHP__FRA_2017-06-30/CONTOURS-IRIS/1_DONNEES_LIVRAISON_2016/CONTOURS-IRIS_2-1_SHP_LAMB93_FE-2016/CONTOURS-IRIS.shp")

        # Change projection
        self.iris = self.iris.to_crs(epsg='4326')

        # Add population
        print("Get population counts per departement...")
        self.population_2014 = pd.read_excel("data/population_iris/base-ic-evol-struct-pop-2014.xls", skiprows=4, header=1)

        self.pop_france = self.population_2014["P14_POP"].sum()
        self.pop_dep = self.population_2014.groupby("DEP")["P14_POP"].sum()
        self.nb_circo = 335 * self.pop_dep / self.pop_france
        self.nb_circo_int = self.nb_circo.astype('int')

    def calculate_circonscripitons_per_departement(self):
        # distribute circonscription by departement
        df_rep = pd.DataFrame()
        df_rep['nb_circo'] = self.nb_circo.values
        df_rep['population'] = self.pop_dep.values
        df_rep['nb_circo_int'] = self.nb_circo_int.values
        df_rep['nb_circo_int'] = df_rep['nb_circo_int'].replace(0, 1)
        df_rep['dep'] = self.population_2014.groupby("DEP")["DEP"]
        rest = int(df_rep['nb_circo'].sum() - df_rep['nb_circo_int'].sum()) + 1
        df_rep['nb_circo_reste'] = df_rep['nb_circo'] - df_rep['nb_circo_int']
        df_rep = df_rep.sort_values('nb_circo_reste', ascending=False)
        df_rep['nb_circo_reste_arrondi'] = (df_rep['nb_circo_reste'] >= df_rep['nb_circo_reste'].nlargest(n=rest).min()).astype('int') 
        df_rep['circo_total'] = df_rep['nb_circo_int'] + df_rep['nb_circo_reste_arrondi'] 
        df_rep = df_rep.sort_values('dep')

        # get rid of corsica, north and dom-tom
        df_final = df_rep.drop(df_rep.index[[28, 29, 95, 96, 97, 98, 99]]).copy()
        df_final['population'] = (df_final['population']/df_final['circo_total']).astype('int')
        df_final.index = range(len(df_final.index))

        self.df_final = df_final

    def prepare_atoms(self, by_departement=True, granualrity="iris"):
        """
            Atoms are the smallest units that are used to build circonscriptions.

            Filter by:
                + by_departement: By departement or all France
                + granualrity: Use commune, canton, or iris
        """

        iris_filtered = {}

        if by_departement:
            for i in range(1, 95):
                if i < 10:
                    departement = "0"+str(i)

                else:
                    departement = str(i)
                if i != 20:
                    iris_filtered[i] = self.iris[self.iris["CODE_IRIS"].str.startswith(departement)].copy()
            else:
                iris_filtered[0] = self.iris.copy()

        self.population_2014["CODE_IRIS"] = self.population_2014["IRIS"]

        dept = 1

        for key, value in iris_filtered.items():

                value.loc[:,'P14_POP'] = self.population_2014['P14_POP']
                value.loc[:, 'departement_iris'] = dept
                dept = dept + 1
                value.loc[:, 'centroid_lng'] = value["geometry"].centroid.apply(lambda x: x.x)
                value.loc[:, 'centroid_lat'] = value["geometry"].centroid.apply(lambda x: x.y)

        self.iris_filtered = iris_filtered

    def generate_maps(self):
        mapa = folium.Map([46.575859, 0.290518],
                          zoom_start=9,
                          tiles='cartodbpositron')

        map_filtered = {}
        k = 320
        count = 1

        # for k in range(300,600,25):
        for key, value in self.iris_filtered.items():
            print(key)

            # get rid of corsica and north (problem with map generation)
            points = []
            if key < 20:
                nb = self.df_final['circo_total'][key-1]
                pop = self.df_final['population'][key-1]
            if key > 20:
                nb = self.df_final['circo_total'][key-2]
                pop = self.df_final['population'][key-2]

            for idx, row in value.iterrows():
                points.append({"coords": np.array([float(row['centroid_lng']), float(row['centroid_lat'])]), \
                              "w": int(row["P14_POP"]), "zip": row['CODE_IRIS'], "state": row["departement_iris"]})
            centers = data_weighted_kmeans.randomize_initial_cluster(points, nb)

            print("weights")
            points, centers, it_num = data_weighted_kmeans.kmeans_evolution_weighted(points, centers, nb, it_max=1000, weight_step_scale=10)
            points_df = pd.DataFrame.from_dict(points)
            points_df["CODE_IRIS"] = points_df["zip"]
            points_df["coords"] = "aaa"
            result = value.merge(points_df, how='inner', on=['CODE_IRIS', 'CODE_IRIS'])
            print("Dissolve")
            simplified_map = result.dissolve(by='c')
            simplified_map.crs = result.crs
            print("Done")
            simplified_map["colour"] = ["#%06x" % random.randint(0, 0xFFFFFF) for i in range(0,nb)]
            points = folium.features.GeoJson(simplified_map,  style_function=lambda feature: {
                                             'fillColor': feature['properties']['colour'],
                                             'color': "#000000",
                                             'weight': 1,
                                             'fillOpacity': 0.5,
                                             })
            map_filtered["map{0}".format(key)] = points
            mapa.add_children(points)

            for i in range(0, len(centers)):
                center = centers[i]
                folium.Marker([center["coords"][1], center["coords"][0]],
                              popup="population :"+str(pop),
                              icon=folium.Icon(color='red', icon='info-sign')).add_to(mapa)

            if key > 4:
                break

        fn = 'map_'+str(k)+'circo.html'
        mapa.save(fn)
