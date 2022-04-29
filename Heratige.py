# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 19:29:50 2022

@author: tiesh

This script pulls two pieces of open source code together to adapt data from the Farmtrace sever into that necessary of an existing code

The family tree code is found on https://gist.github.com/AhsenParwez/eb0fd2450ad230c5fb30d99d12c2693f
"""

#initially import necessary packages
import pyodbc
import pandas as pd
from graphviz import Digraph


#connect and pull data from azure server
server = 'Farmtrace' 
database = 'FarmTrace.Cows' 
username = 'yourusername' 
password = 'databasename'  
cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()

#all columns are taken from the database
query = "SELECT *, FROM Farmtrace.cow;"
df = pd.read_sql(query, cnxn)

#create new dataframe in the form used by the familytree script
#Assigning each cows parents and definining the earliest ancestors to start the list
ancestry = pd.DataFrame(columns = ['Person 1', 'Relation', 'person_2', 'Gender'])
i = 1
for cow in df['CowUNID']:   
    father = df.iloc[cow,'CowUNID_Father']
    mother = df.iloc[cow,'CowUNID_Mother']
    
    if father is None and mother is None:
        ancestry.iloc[i]['Person 1'] = cow
        ancestry.iloc[i]['Relation'] = 'earliest_Ancestor'
        ancestry.iloc[i]['Gender'] = df.iloc[cow,'sex']
    if father:
        ancestry.iloc[i]['Person 1'] = cow
        ancestry.iloc[i]['Relation'] = 'child'
        ancestry.iloc[i]['Gender'] = df.iloc[cow,'sex']
        ancestry.iloc[i]['person_2'] = father
        i=+1
        ancestry.iloc[i]['Person 1'] = cow
        ancestry.iloc[i]['Relation'] = 'child'
        ancestry.iloc[i]['Gender'] = df.iloc[cow,'sex']
        ancestry.iloc[i]['Person 2'] = mother
        #defining spouses aka a two parents to follow a family tree
        i=+1 
        ancestry.iloc[i]['Person 1'] = father
        ancestry.iloc[i]['Relation'] = 'spouse'
        ancestry.iloc[i]['Gender'] = 'male'
        ancestry.iloc[i]['Person 2'] = mother
    i=+1


#This is the preset package that would make the family tree
earl_ans = ancestry.loc[ancestry['Relation'] == 'Earliest Ancestor', 'Person 1'].iloc[0]
ancestry['recorded_ind'] = 0    # Flag for indicating individuals whose data has been recorded in the tree

incomp = [earl_ans]
comp = []

dot = Digraph(comment = 'Ancestry', graph_attr = {'splines':'ortho'})
node_nm = []

# Initializing first node
det = str(ancestry.loc[ancestry['Person 1'] == earl_ans, 'Details'][0])
g = ancestry.loc[ancestry['Person 1'] == earl_ans, 'Gender'][0]
sh = 'rect' if g == 'M' else 'ellipse'
dot.node(earl_ans, earl_ans, tooltip = det, shape = sh)
node_nm.append(earl_ans)

ancestry.loc[ancestry['Person 1'] == earl_ans, 'recorded_ind'] = 1

# max_iter should be greater than number of generations
max_iter = 5

for i in range(0, max_iter):
    print(i)
    temp = ancestry[ancestry['recorded_ind'] == 0]

    if len(temp) == 0:      # Break loop when all individuals have been recorded
        break
    else:
        temp['this_gen_ind'] = temp.apply(lambda x: 1 if x['Person 2'] in incomp else 0, axis = 1)

        # Spouse Relationship
        this_gen = temp[(temp['this_gen_ind'] == 1) & (temp['Relation'] == 'Spouse')]
        if len(this_gen) > 0:
            for j in range(0, len(this_gen)):
                per1 = this_gen['Person 1'].iloc[j]
                per2 = this_gen['Person 2'].iloc[j]
                det = str(this_gen['Details'].iloc[j])
                g = this_gen['Gender'].iloc[j]
                sh = 'rect' if g == 'M' else 'ellipse'
                with dot.subgraph() as subs:
                    subs.attr(rank = 'same')
                    subs.node(per1, per1, tooltip = det, shape = sh, fillcolor = "red")
                    node_nm.append(per1)
                    subs.edge(per2, per1, arrowhead = 'none', color = "black:invis:black")

        # Child Relationship
        this_gen = temp[(temp['this_gen_ind'] == 1) & (temp['Relation'] == 'Child')]
        if len(this_gen) > 0:
            for j in range(0, len(this_gen)):
                per1 = this_gen['Person 1'].iloc[j]
                per2 = this_gen['Person 2'].iloc[j]
                det = str(this_gen['Details'].iloc[j])
                g = this_gen['Gender'].iloc[j]
                sh = 'rect' if g == 'M' else 'ellipse'
                dot.node(per1, per1, tooltip = det, shape = sh)
                node_nm.append(per1)
                dot.edge(per2, per1)

        comp.extend(incomp)
        incomp = list(temp.loc[temp['this_gen_ind'] == 1, 'Person 1'])
        ancestry['recorded_ind'] = temp.apply(lambda x: 1 if (x['Person 1'] in incomp) | (x['Person 1'] in comp) else 0, axis = 1)

dot.format = 'svg'
dot.render('sample_ancestry.gv.svg', view = True)
