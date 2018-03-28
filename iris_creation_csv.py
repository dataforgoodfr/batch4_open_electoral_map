# -*- coding: utf-8 -*-
import pandas as pd 
import csv

data_pop = pd.read_csv("data_iris.csv", encoding= "Latin1")
output = csv.writer(open("iris_POP15P.csv", "w" ))

# setting target population
data_pop["P14_POP15P"] = data_pop["P14_POP"] - data_pop["P14_POP0014"]
print(data_pop["P14_POP15P"])

# setting strings on data_pop to make code iris == code shapefile
data_pop["IRIS"] = data_pop["IRIS"].apply(str)
data_pop["DCOMIRIS"] = pd.Series()
data_pop["DCOMIRIS"] = data_pop["IRIS"].str.zfill(9)
print(data_pop.head(5))


# setting df to export
data_final = pd.DataFrame()
data_final["DCOMIRIS"] = data_pop["DCOMIRIS"]
data_final["P14_POP"] = data_pop["P14_POP"].apply(int)
data_final["P14_POP15P"] = data_pop["P14_POP15P"].apply(int)
data_final["REG"] = data_pop["REG"]
data_final["DEP"] = data_pop["DEP"]
print(data_final.head(5))

for index, row in data_final.iterrows():
    output.writerow(row)