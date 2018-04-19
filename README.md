# Redécoupage citoyen

_Nous votons, nous dessinons_

[Toutes les infos](http://quatrecentquatre.org/)


---

## Iteration 0

18 / 04 / 2018

### Data

- `data_iris.csv`: French population in 2014 by [IRIS](https://www.insee.fr/en/metadonnees/definition/c1523) with all variables ([source](https://www.insee.fr/fr/statistiques/3137409))
- `data_iris_subsetpop.csv`: Subset with just main population variable
- `CONTOURS-IRIS_2-1_SHP_LAMB93_FE-2016`: IRIS shapefile, Lambert-93 projection, metropolitan France (too big for Git so we put it [online here](https://nextcloud.f0rk.fr/index.php/s/qpH2FPS5EcXtTiy), [source](http://professionnels.ign.fr/contoursiris))

### Tools

- JupyterLab / [Jupyter Notebook](http://jupyter.org/) (to wrangle with data, run and present results)
- [Binder](http://mybinder.org/) (to run and share the Notebook online)
- GitHub (here!)


### Criteria

A web interface (e.g. a Jupyter notebook on Binder) displaying a map of France divided in X _circonscriptions_, with a slider to change their number. _Circonscriptions_ must be **equal in population** **compact** (no weird shapes) and **continuous** (not broken in different parts). As much as possible they must not go out of _commune_ and _départements_ limits.
