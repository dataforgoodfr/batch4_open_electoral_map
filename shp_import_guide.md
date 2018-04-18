# Guide pour importer et travailer avec des SHP files en PSQL

Quelques notes: 
+ Il y a 49 404 shapes IRIS
+ Il y a une '-' dans le nom de la table donc il faut utiliser les " autour du nom de la table dans les requetes SQL
+ Plusieurs tables sont créer par shp2pgsql

## Setup

### Installer postgres et postgis
```
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgis
```

### Tester

Commencer le service, changer au nouveau user postgres, essayer de vous connecter au serveur avec le client psql. 
```
service postgresql start
su postgres
psql
```

Vous devrais être dans le console psql :
```
psql (9.5.12)
Type "help" for help.

postgres=# 
```

### Créer une nouvelle base de données

Comme le user postgres, créer une nouvelle base de données, fermer la session psql, et connecter à la nouvelle base de données. 

```
psql
CREATE DATABASE map;
\q
psql map
```

### Setup Extension PostGIS sur la base de données

Dans la base de données map, initialiser l'extension postgis.

```sql
CREATE EXTENSION postgis;
-- Enable Topology
CREATE EXTENSION postgis_topology;
-- Enable PostGIS Advanced 3D 
-- and other geoprocessing algorithms
-- sfcgal not available with all distributions
CREATE EXTENSION postgis_sfcgal;
-- fuzzy matching needed for Tiger
CREATE EXTENSION fuzzystrmatch;
-- rule based standardizer
CREATE EXTENSION address_standardizer;
-- example rule data set
CREATE EXTENSION address_standardizer_data_us;
-- Enable US Tiger Geocoder
CREATE EXTENSION postgis_tiger_geocoder;
```

Et quit psql
> \q

## Importer le shape file

Télécharger le shape file et extract (source: https://wxs-telechargement.ign.fr/1yhlj2ehpqf3q6dt6a2y7b64/telechargement/inspire/CONTOURS-IRIS-2017-06-30$CONTOURS-IRIS_2-1__SHP__FRA_2017-06-30/file/CONTOURS-IRIS_2-1__SHP__FRA_2017-06-30.7z)

```
wget [PATH]
7z x CONTOURS-IRIS_2-1__SHP__FRA_2017-06-30.7z
```

Importer le shape file avec l'outil shp2pgsql qui devrait etre installer avec postgis. 

```
cd CONTOURS-IRIS/1_DONNEES_LIVRAISON_2016/CONTOURS-IRIS_2-1_SHP_LAMB93_FE-2016
shp2pgsql -I -s 2154 CONTOURS-IRIS.shp | psql -d map
```
(Projection : http://spatialreference.org/ref/epsg/rgf93-lambert-93/)


### Tester que l'import a bien marcher

```sql
select ST_X(ST_Centroid(geom)) from "contours-iris" limit 3;
select ST_X(ST_TRANSFORM(ST_Centroid(geom),4326)) as LONG, ST_Y(ST_TRANSFORM(ST_Centroid(geom),4326)) AS LAT from "contours-iris" limit 10;
````

Exemple output:
```
st_x       
------------------
 842103.058677527
 267733.551330488
 650847.326144646
```

Note: 
+ ST_X / ST_Y : Get the lat/long components
+ ST_TRANSFORM : convertir en projection type 4326 (WGS84) qui est en degrés
+ ST_Centroid : calcul du centroid


### Créer et populer les nouvelles colonnes pour le centroid
```sql
ALTER TABLE "contours-iris" ADD COLUMN centroid geometry;
ALTER TABLE "contours-iris" ADD COLUMN centroid_lat decimal;
ALTER TABLE "contours-iris" ADD COLUMN centroid_lng decimal;

UPDATE "contours-iris" set centroid = ST_Centroid(geom);
UPDATE "contours-iris" set centroid_lng = ST_X(ST_TRANSFORM(ST_Centroid(geom),4326));
UPDATE "contours-iris" set centroid_lat = ST_Y(ST_TRANSFORM(ST_Centroid(geom),4326));
```



### Test les nouvelles colonnes

```sql
select * from "contours-iris" where gid=49015;
```

Output : 
```
49015 | 69385     | Lyon 5e Arrondissement | 0102 | 693850102 | Saint-Jean | H        | 01060000206A0800000100000001
03000000010000001E0000003333333327B42941000000802EDF58413333333328B429416666664629DF58413333333320B42941000000200DDF5
841666666661BB429410000004006DF58419A99999918B42941CDCCCCEC01DF58416666666614B4294100000080F7DE5841CDCCCCCC05B4294100
0000C0DADE584166666666F2B32941CDCCCC8CD5DE584166666666B2B3294133333393C4DE5841CDCCCCCC03B32941333333339EDE584148E17A9
403B32941666666269EDE5841CDCCCCCCF2B22941000000009FDE584100000000BBB22941000000E0A1DE584166666666B2B2294100000040A2DE
584166666666ADB22941CDCCCCECA0DE58416666666690B22941333333B3A2DE58416666666604B229419A999939C0DE5841666666661EB229419
A999919C7DE5841CDCCCCCC34B2294100000020D3DE5841CDCCCCCCDCB1294166666626DCDE58413333333396B1294166666666E0DE5841000000
009AB1294100000080E1DE58419A9999999EB12941666666A616DF584100000000B9B129419A9999B929DF5841CDCCCCCCC1B12941000000E029D
F5841CDCCCCCC6CB329419A9999395FDF58410AD7A3F06CB32941C3F5283C5FDF58419A9999996DB32941666666265FDF5841CDCCCCCC02B42941
666666063ADF58413333333327B42941000000802EDF5841 | 01010000206A0800001BFB0A1EEEB2294173C19621FFDE5841 | 45.7630388683
502 | 4.82841501765631

```
