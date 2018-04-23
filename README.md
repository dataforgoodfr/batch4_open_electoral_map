# Redécoupage citoyen

_Nous votons, nous dessinons_

[Toutes les infos](http://quatrecentquatre.org/)


---

## Iteration 0

18 / 04 / 2018

### Data

#### IRIS Data
- `data_iris.csv`: French population in 2014 by [IRIS](https://www.insee.fr/en/metadonnees/definition/c1523) with all variables ([source](https://www.insee.fr/fr/statistiques/3137409))
- `data_iris_subsetpop.csv`: Subset with just main population variable
- `CONTOURS-IRIS_2-1_SHP_LAMB93_FE-2016`: IRIS shapefile, Lambert-93 projection, metropolitan France (too big for Git so we put it [online here](https://nextcloud.f0rk.fr/index.php/s/qpH2FPS5EcXtTiy), [source](http://professionnels.ign.fr/contoursiris))

#### Existing electoral districts 
- `data/circonscriptions-existants/france-circonscriptions-legislatives-2012`: Map of exisiting electoral districts. Produced by L'Atelier de cartographie de SciencesPo, based on the work of Toxicode. ([source](https://www.data.gouv.fr/fr/datasets/carte-des-circonscriptions-legislatives-2012-et-2017/#_), [Toxicode](http://www.toxicode.fr/circonscriptions)). Note: The precision of this map is uncertain.


#### Other Data
- Map of departements, created by OpenStreetMaps ([source](https://www.data.gouv.fr/en/datasets/contours-des-departements-francais-issus-d-openstreetmap/))
- Population per departement produced by the INSEE ([source](https://www.insee.fr/fr/statistiques/1893198)) 

    
### Tools

- JupyterLab / [Jupyter Notebook](http://jupyter.org/) (to wrangle with data, run and present results)
- [Binder](http://mybinder.org/) (to run and share the Notebook online)
- GitHub (here!)


### Criteria

A web interface (e.g. a Jupyter notebook on Binder) displaying a map of France divided in X _circonscriptions_, with a slider to change their number. _Circonscriptions_ must be **equal in population** **compact** (no weird shapes) and **continuous** (not broken in different parts). As much as possible they must not go out of _commune_ and _départements_ limits.
