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

        # Add population. 
        print("Get population counts per departement...")
        self.population_2014 = pd.read_excel("data/population_iris/base-ic-evol-struct-pop-2014.xls", skiprows=4, header=1)
        self.population_2014["CODE_IRIS"] = self.population_2014["IRIS"]
        self.iris = self.iris.merge(self.population_2014, how='inner', on=["CODE_IRIS"])

    def calculate_circonscripitons_per_departement(self):
        # Population per departement
        self.pop_france = self.population_2014["P14_POP"].sum()
        self.pop_dep = self.population_2014.groupby("DEP")["P14_POP"].sum()
        self.nb_circo = 335 * self.pop_dep / self.pop_france
        self.nb_circo_int = self.nb_circo.astype('int')

        # distribute circonscription by departement
        df_rep = pd.DataFrame()
        df_rep['nb_circo'] = self.nb_circo
        df_rep['population'] = self.pop_dep
        df_rep['nb_circo_int'] = self.nb_circo_int
        df_rep['nb_circo_int'] = df_rep['nb_circo_int'].replace(0, 1)

        rest = int(df_rep['nb_circo'].sum() - df_rep['nb_circo_int'].sum()) + 1
        df_rep['nb_circo_reste'] = df_rep['nb_circo'] - df_rep['nb_circo_int']
        df_rep = df_rep.sort_values('nb_circo_reste', ascending=False)
        df_rep['nb_circo_reste_arrondi'] = (df_rep['nb_circo_reste'] >= df_rep['nb_circo_reste'].nlargest(n=rest).min()).astype('int') 
        df_rep['circo_total'] = df_rep['nb_circo_int'] + df_rep['nb_circo_reste_arrondi']
        df_rep = df_rep.sort_index()

        # get rid of dom-tom
        df_final = df_rep.drop(["971", "972", "973", "974"]).copy()
        df_final['population_circo'] = (df_final['population']/df_final['circo_total']).astype('int')

        # df_final = df_rep
        self.df_final = df_final

    def prepare_atoms(self, by_departement=True, granualrity="iris"):
        """
            Atoms are the smallest units that are used to build circonscriptions.

            Filter by:
                + by_departement: By departement or all France
                + granualrity: Use commune, canton, or iris
        """

        # Build the atom units (commune, iris, cantons, etc)
        if granualrity == "commune":
            print("Dissolve the communes...")
            commune_df = self.iris.copy()

            commune_df["NOM_COM_FULL"] = commune_df["CODE_IRIS"].str[:2] + "_" + commune_df["NOM_COM"]

            commune_df = commune_df.dissolve("NOM_COM_FULL", aggfunc="sum")
            commune_df.crs = self.iris.crs

            # Calcul le centroid des nouveaux atoms
            commune_df.loc[:, 'centroid_lng'] = commune_df["geometry"].centroid.apply(lambda x: x.x)
            commune_df.loc[:, 'centroid_lat'] = commune_df["geometry"].centroid.apply(lambda x: x.y)

            commune_df["NOM_COM_FULL"] = commune_df.index
            commune_df["ATOM_ID"] = commune_df["NOM_COM_FULL"]

            atom = commune_df.copy()
        else:
            atom = self.iris.copy()
            atom["ATOM_ID"] = atom["CODE_IRIS"]

        # Build the dictionnary of sets of atoms within which we build circonscriptions
        # (departement or national level)
        print("Group the atom sets...")
        iris_filtered_dep = {}
        # iris_filtered_metro = {"metro": pd.DataFrame(), "corse": pd.DataFrame()}
        iris_filtered_metro = {"corse": pd.DataFrame(), "metro": pd.DataFrame()}

        for i in range(1, 96):
            dep = str(i).zfill(2)

            if i == 20:

                dep = "2A"
                dep_atom = atom[atom["ATOM_ID"].str.startswith(dep)].copy()
                iris_filtered_dep[dep] = dep_atom.copy()
                corse = iris_filtered_metro["corse"]
                iris_filtered_metro["corse"] = corse.append(dep_atom.copy())

                dep = "2B"
                dep_atom = atom[atom["ATOM_ID"].str.startswith(dep)].copy()
                iris_filtered_dep[dep] = dep_atom.copy()
                corse = iris_filtered_metro["corse"]
                iris_filtered_metro["corse"] = corse.append(dep_atom.copy())
            else:
                dep_atom = atom[atom["ATOM_ID"].str.startswith(dep)].copy()
                iris_filtered_dep[dep] = dep_atom.copy()
                metro = iris_filtered_metro["metro"]
                iris_filtered_metro["metro"] = metro.append(dep_atom.copy())

        for key, value in iris_filtered_dep.items():
            value.loc[:, 'centroid_lng'] = value["geometry"].centroid.apply(lambda x: x.x)
            value.loc[:, 'centroid_lat'] = value["geometry"].centroid.apply(lambda x: x.y)

        for key, value in iris_filtered_metro.items():
            value.loc[:, 'centroid_lng'] = value["geometry"].centroid.apply(lambda x: x.x)
            value.loc[:, 'centroid_lat'] = value["geometry"].centroid.apply(lambda x: x.y)

        if by_departement:
            self.iris_filtered = iris_filtered_dep
        else:
            self.iris_filtered = iris_filtered_metro

    def generate_maps(self, outname):
        mapa = folium.Map([46.575859, 0.290518],
                          zoom_start=9,
                          tiles='cartodbpositron')

        map_filtered = {}

        # for k in range(300,600,25):
        for key, atom_df in self.iris_filtered.items():
            print(key)

            # get rid of corsica and north (problem with map generation)
            points = []
            if key == "metro":
                nb = self.df_final['circo_total'].sum() - (self.df_final.loc["2A","circo_total"] + self.df_final.loc["2B","circo_total"])
                # pop = self.df_final['population_circo'].sum()
            elif key == "corse":
                nb = self.df_final.loc["2A","circo_total"] + self.df_final.loc["2B","circo_total"]
                # pop = self.df_final['population_circo'].sum()
            else:
                nb = self.df_final['circo_total'][key]
                # pop = self.df_final['population_circo'][key]

            # Build points
            for idx, row in atom_df.iterrows():
                points.append({"coords": np.array([float(row['centroid_lng']), float(row['centroid_lat'])]), \
                              "w": int(row["P14_POP"]), "ATOM_ID": row['ATOM_ID']})

            # Calculate clusters
            centers = data_weighted_kmeans.randomize_initial_cluster(points, nb)
            points, centers, it_num = data_weighted_kmeans.kmeans_evolution_weighted(points, centers, nb, it_max=1000, weight_step_scale=10)
            points_df = pd.DataFrame.from_dict(points)
            # points_df["ATOM_ID"] = points_df["atom_id"]

            result = atom_df.merge(points_df, how='inner', on=['ATOM_ID', 'ATOM_ID'])

            # Merge atoms by circonscription
            simplified_map = result.dissolve(by='c')
            simplified_map.crs = result.crs

            # Draw
            simplified_map["colour"] = ["#%06x" % random.randint(0, 0xFFFFFF) for i in range(0,nb)]
            points = folium.features.GeoJson(simplified_map[["geometry", "colour"]],  style_function=lambda feature: {
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
                              popup="population :"+str(center["pop"]),
                              icon=folium.Icon(color='red', icon='info-sign')).add_to(mapa)

        fn = outname + ".html"
        mapa.save(fn)
