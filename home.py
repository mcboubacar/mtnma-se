#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 12:43 2025

@author: mboubacar
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import io
import datetime
from pathlib import Path
from PIL import Image  # Pour charger l'image
from utils.data import load_data
from utils.dataviz import vizAggrid


st.set_page_config(page_title="Suivi des Activités MTNMA", layout="wide")
# Obtenir le chemin absolu du répertoire du script
script_dir = Path(__file__).parent.resolve()

# ⏱️ Constante pour les libellés
MAX_LIBELLE_LEN = 30
def tronquer(x): return x if len(x) < MAX_LIBELLE_LEN else x[:MAX_LIBELLE_LEN - 3] + "..."

# Charger le logo
logo = Image.open("SCEAU MAURITANIE.jpg")

col1, col2 = st.columns([1,4])
with col1:
    st.image(logo, width=80)  # Ajustez la largeur
with col2:
    st.title("📊 Tableau de bord du suivi-evaluation")

st.markdown(
    "<hr style='border: none; height: 2px; background-color: blue;'>",
    unsafe_allow_html=True
    )      

# Chargement des données

pathdatafile = Path("datafile.xlsx").resolve()
if pathdatafile.exists():
    timestamp_creation = pathdatafile.stat().st_ctime
    date_creation_file = datetime.datetime.fromtimestamp(timestamp_creation)
    affichage_date=date_creation_file.strftime("%d/%m/%Y à %H:%M:%S")
    # Filter pour chargement des données
    with st.sidebar:
        st.subheader(" 🔍 Selection des données")
        # Options avec un choix vide
        options = [f"Dernier jeux de données le {affichage_date}", "Nouveau jeux de données"]
        choix = st.radio("Sélectionner le mode de chargement :", options, index=0)
        st.markdown(
                "<hr style='border: none; height: 2px; background-color: blue;'>",unsafe_allow_html=True
        )     
        if(choix==f"Dernier jeux de données le {affichage_date}"):
            df = pd.read_excel(pathdatafile)
        else:
            df = load_data()
            filedest=script_dir / "datafile.xlsx"
            df.to_excel(filedest,index=False)
else:
    df = load_data()
    filedest=script_dir / "datafile.xlsx"
    df.to_excel(filedest,index=False)

# Créer un masque pour les valeurs à conserver
df["Domaine"] = df["Domaine"].astype(str).str.strip()
df["Responsable"] = df["Responsable"].astype(str).str.strip()
df["Activité"] = df["Activité"].astype(str).str.strip()

valeurs_exclues = ["nan", "NaN", "None", ""]

mask = (
    ~df["Domaine"].isin(valeurs_exclues) &
    ~df["Responsable"].isin(valeurs_exclues) &
    ~df["Activité"].isin(valeurs_exclues)
)
df = df[mask]

# Maj de certaines donnees
df['Statut']=df['Statut'].replace(["En cours d'execution","encours"],"En cours")
df["Date limite"] = pd.to_datetime(df["Date limite"], errors="coerce")
df["Tache"] = df["Tache"].astype(str).str.strip()
df["Taux réalisation"] = df["Taux réalisation"].astype(str).str.strip()
df.loc[df['Tache'].isin(["nan", "None", "NaN", ""]), 'Tache'] = 'UNDEFINED'
df.loc[df['Taux réalisation'].isin(["nan", "None", "NaN", ""]), 'Taux réalisation'] = 0
# Supprimer les doublons de ["responsable","domaine","activite","tache"]
df = df.drop_duplicates(subset=['Responsable', 'Domaine', 'Activité', 'Tache'], keep='first')

#df["Année"] = df["Date limite"].dt.year.fillna(0).astype(int)
# maj du statut et taux de realisation
df["Statut"] = df["Statut"].astype(str).str.strip()
df.loc[df['Statut'].isin(["nan", "None", "NaN", ""]) & (df['Taux réalisation'] == 0), 'Statut'] = 'En attente'
df.loc[df['Statut'].isin(["nan", "None", "NaN", ""]) & ((df['Taux réalisation'] > 0)&(df['Taux réalisation'] < 100)), 'Statut'] = 'En cours'
df.loc[df['Statut'].isin(["nan", "None", "NaN", ""]) & (df['Taux réalisation'] == 100), 'Statut'] = 'Terminée'
# st.dataframe(df)
# st.write("statut vide")
# st.dataframe(df[df['Statut'].isin(["nan", "NaN", "None", ""])])
# Sidebar
with st.sidebar:
    st.header("🔍 Filtres")
    domaines = st.multiselect("Domaine", options=sorted(df["Domaine"].unique()))
    responsables = st.multiselect("Responsable", options=sorted(df["Responsable"].unique()))
    #annees = st.multiselect("Période (Année)", options=sorted(df["Année"].unique()))
    statuts = st.multiselect("Statut", options=sorted(df["Statut"].unique()))

# Si aucun filtre sélectionné, on prend tout
mask = pd.Series(True, index=df.index)
if domaines:
    mask &= df["Domaine"].isin(domaines)
if responsables:
    mask &= df["Responsable"].isin(responsables)
#if annees:
#    mask &= df["Année"].isin(annees)
if statuts:
    mask &= df["Statut"].isin(statuts)

filtered_df = df[mask]

# Gestion du cas vide
if filtered_df.empty:
    st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# Vue hiérarchique Activité > Tâche
activites = filtered_df.groupby(["Responsable","Domaine","Activité"]).agg(
    Tâches_totales=("Tache", "count"),
    Tâches_realisees=("Statut", lambda x: (x == "Terminée").sum()),
    Tâches_en_cours=("Statut", lambda x: (x == "En cours").sum()),
    Tâches_en_attente=("Statut", lambda x: (x == "En attente").sum()),
    Date_limite=("Date limite", "max")
).reset_index()
# st.write("xxxxx")
# st.dataframe(activites)
# st.write(activites[["Tâches_totales","Tâches_realisees","Tâches_en_cours","Tâches_en_attente"]].sum(axis=0))
activites["Taux réalisation"] = round(100 * activites["Tâches_realisees"] / activites["Tâches_totales"], 1)

conditions = [
    activites['Tâches_totales'] == activites['Tâches_realisees'],
    activites['Tâches_totales'] == activites['Tâches_en_attente']
]
choices = ["Terminée","En attente"]

activites['Statut'] = np.select(conditions, choices, default="En cours")

#st.write("activites processed: ",activites)

# st.markdown("##### 📋 Activités en fonction des filtres")
nwactivites=activites.drop(["Tâches_totales","Tâches_realisees","Tâches_en_cours","Tâches_en_attente"],axis=1)
vizAggrid(nwactivites,"📊 Tableau des activités")
st.markdown(
    "<hr style='border: none; height: 2px; background-color: blue;'>",
    unsafe_allow_html=True
)      

# 🎯 Statistiques globales
st.markdown("##### 📋 Les KPI")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🧩 Total Activités", activites.shape[0])
col2.metric("✅ Activités Terminées", (activites["Taux réalisation"] == 100).sum())
col3.metric("✅ Activités En cours", (activites[activites["Statut"] == "En cours"].shape[0]))
col4.metric("⏰ Activités en Retard", ((activites["Date_limite"].dt.tz_localize(None) < pd.Timestamp.today()) & (activites["Taux réalisation"] < 100)).sum())
col5.metric("⏰ Activités en Attente", (activites[activites["Statut"] == "En attente"].shape[0]))
# 📥 Export Excel
# with st.expander("⬇️ Télécharger les données filtrées"):
#     output = io.BytesIO()
#     activites.to_excel(output, index=False)
#     st.download_button("Télécharger en Excel", data=output.getvalue(), file_name="activites_filtrees.xlsx")

st.markdown(
    "<hr style='border: none; height: 2px; background-color: blue;'>",
    unsafe_allow_html=True
    )      


# Graphique 1 : Activités par domaine
st.subheader("📌 Nombre d'Activités par Domaine")
activites["Domaine-trq"] = activites["Domaine"].apply(tronquer)
fig_domaine = px.bar(
    activites.groupby(["Domaine-trq","Statut"]).size().reset_index(name="Nombre d'activités"),
    x="Domaine-trq", y="Nombre d'activités", 
    text_auto=True, color="Statut",
    labels={'Domaine-trq': 'Domaine'},
    width=800,height=500,
    color_discrete_map={"Terminée": "#2ca02c", "En cours": "#Cca02c"},
)
st.plotly_chart(fig_domaine, use_container_width=True)

# Graphique 2 : Activités par responsable
st.subheader("📌 Nombre d'Activités par Rsponsable")
activites["Resp-trq"] = activites["Responsable"].apply(tronquer)
fig_resp = px.bar(
    activites.groupby(["Resp-trq","Statut"]).size().reset_index(name="Nombre d'activités"),
    x="Resp-trq", y="Nombre d'activités", 
    text_auto=True, color="Statut",
    labels={'Resp-trq': 'Responsable'},
    width=800,height=500,
    color_discrete_map={"Terminée": "#2ca02c", "En cours": "#Cca02c"},
)
st.plotly_chart(fig_resp, use_container_width=True)

# Graphique 3 : Répartition des activites par statuts
if  not ((filtered_df["Tache"]=="Sans tâche").all()):
    st.subheader("📋 Répartition des Activites par Statut")
    fig_statut = px.histogram(
        activites.groupby(["Statut"]).size().reset_index(name="Nombre d'activités"), 
        x="Statut", y="Nombre d'activités",
        text_auto=True, color="Statut", barmode="group",
        color_discrete_map={"Terminée": "#2ca02c", "En cours": "#Cca02c"},
        )
    fig_statut.update_traces(textposition='outside')
    st.plotly_chart(fig_statut, use_container_width=True)

# Graphique 4 : Taux d'exécution

activites["libellé activité"] = activites["Activité"].apply(tronquer)
activites_filtrees = activites[activites["Taux réalisation"] > 0]
if len(activites_filtrees)!=0:
    st.subheader("✅ Taux de réalisation des Activités(taux > 0)")
    fig_exec = px.bar(
        #activites_filtrees.sort_values("Taux réalisation", ascending=False),
        activites_filtrees,
        y="Taux réalisation", x="libellé activité", orientation="v", 
        text_auto=True,color_continuous_scale="#2ca02c"
    )
    fig_exec.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig_exec, use_container_width=True)

# Graphique 5 : Activités en retard
#st.subheader("⏳ Activités en Retard")
# enlever la TZ de date imite pour la comparer avec timestamp.today()
activites["Date_limite"] = activites["Date_limite"].dt.tz_localize(None)
retard = activites[
    (activites["Date_limite"] < pd.Timestamp.today()) &
    (activites["Taux réalisation"] < 100)
]

if not retard.empty:
    if retard["Taux réalisation"].sum()==0:
        nwretard=retard[["Responsable","Domaine","Activité","Date_limite","Taux réalisation","Statut"]]
        vizAggrid(nwretard,"⏳ Activités en Retard")
    else:    
        retard["libellé activité"] = retard["Activité"].apply(tronquer)
        fig_retard = px.bar(
            retard,
            x="libellé activité", y="Taux réalisation", color="Domaine", color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_retard, use_container_width=True)
else:
    st.success("🎉 Aucune activité en retard selon les filtres OU données de suivi non renseignées")

import altair as alt

# Exemple de données
mydata = pd.DataFrame({
    'Activité': ['Achat Serveur', 'Maintenance Réseau', 'Formation équipe', 'Déploiement Cloud'],
    'Montant': [5000, 2000, 1500, 7000],
    'Échéance': pd.to_datetime(['2025-05-01', '2025-04-20', '2025-05-15', '2025-04-25'])
})

# Tri par date d’échéance
data = mydata.sort_values('Échéance')

mychart = alt.Chart(data).mark_bar().encode(
    x=alt.X('Échéance:T', title="Date d'échéance"),
    y=alt.Y('Montant:Q'),
    color=alt.Color('Activité', legend=None),
    tooltip=['Activité', 'Montant', 'Échéance']
).properties(
    title="Montants par activité et date d’échéance"
)

st.altair_chart(mychart, use_container_width=True)