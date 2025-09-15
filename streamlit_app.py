import streamlit as st
import pandas as pd
import os

CSV_FILE = "tasks.csv"

# --- Charger ou initialiser le CSV ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["Tâche", "Responsable", "Date limite", "Statut", "Confirmé"])
    df.to_csv(CSV_FILE, index=False)

# --- Titre principal ---
st.set_page_config(page_title="Gestion des Tâches ANCU", page_icon="✅", layout="centered")
st.title("✅ Gestion des Tâches ANCU")

# --- Affichage du tableau ---
st.subheader("📋 Liste des tâches")
st.dataframe(df)

# --- Formulaire d'ajout ---
st.subheader("➕ Ajouter une nouvelle tâche")
with st.form("add_task"):
    tache = st.text_input("Tâche")
    responsable = st.selectbox("Responsable", ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"])
    date_limite = st.date_input("Date limite")
    statut = st.selectbox("Statut", ["Fini", "Pas fini", "En cours", "Bloqué"])
    confirme = st.checkbox("Confirmé ?")
    submitted = st.form_submit_button("Ajouter")

    if submitted and tache.strip() != "":
        new_task = {
            "Tâche": tache,
            "Responsable": responsable,
            "Date limite": str(date_limite),
            "Statut": statut,
            "Confirmé": "Oui" if confirme else "Non"
        }
        df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        st.success("✅ Tâche ajoutée avec succès !")
        st.experimental_rerun()

# --- Suppression / modification ---
st.subheader("🗑️ Supprimer une tâche")
if not df.empty:
    task_to_delete = st.selectbox("Sélectionner une tâche à supprimer", df["Tâche"].tolist())
    if st.button("Supprimer"):
        df = df[df["Tâche"] != task_to_delete]
        df.to_csv(CSV_FILE, index=False)
        st.warning(f"Tâche '{task_to_delete}' supprimée.")
        st.experimental_rerun()
