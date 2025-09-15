import streamlit as st
import pandas as pd
import os
from datetime import datetime

CSV_FILE = "tasks.csv"

# --- Configuration de la page ---
st.set_page_config(
    page_title="Gestion des Tâches ANCU",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Charger ou initialiser le CSV ---
@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Convertir la date limite en datetime pour le filtrage
        if 'Date limite' in df.columns:
            df['Date limite'] = pd.to_datetime(df['Date limite']).dt.date
        return df
    else:
        return pd.DataFrame(columns=["Tâche", "Responsable", "Date limite", "Statut", "Confirmé"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Charger les données
df = load_data()

# --- CSS personnalisé ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        color: #1E3A8A;
        border-bottom: 2px solid #1E3A8A;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .task-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        background-color: white;
    }
    .status-fini {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .status-pas-fini {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .status-en-cours {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .status-bloque {
        background-color: #E5E7EB;
        color: #374151;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .confirmed {
        color: #065F46;
        font-weight: bold;
    }
    .not-confirmed {
        color: #991B1B;
        font-weight: bold;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar pour la navigation et les filtres ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1E3A8A/FFFFFF?text=ANCU", width=150)
    st.title("Navigation")
    
    # Filtres
    st.subheader("Filtres")
    all_responsibles = ["Tous"] + sorted(df["Responsable"].unique().tolist()) if not df.empty else ["Tous"]
    selected_responsible = st.selectbox("Responsable", all_responsibles)
    
    all_statuses = ["Tous"] + sorted(df["Statut"].unique().tolist()) if not df.empty else ["Tous"]
    selected_status = st.selectbox("Statut", all_statuses)
    
    # Métriques
    st.subheader("Métriques")
    if not df.empty:
        total_tasks = len(df)
        completed_tasks = len(df[df["Statut"] == "Fini"])
        confirmed_tasks = len(df[df["Confirmé"] == "Oui"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total tâches", total_tasks)
        with col2:
            st.metric("Tâches finies", f"{completed_tasks}/{total_tasks}")
        
        st.metric("Tâches confirmées", f"{confirmed_tasks}/{total_tasks}")
    else:
        st.info("Aucune tâche à afficher")

# --- Titre principal ---
st.markdown('<h1 class="main-header">✅ Gestion des Tâches ANCU</h1>', unsafe_allow_html=True)

# --- Tableau des tâches avec filtres ---
st.markdown('<h2 class="section-header">📋 Liste des tâches</h2>', unsafe_allow_html=True)

# Appliquer les filtres
filtered_df = df.copy()
if not df.empty:
    if selected_responsible != "Tous":
        filtered_df = filtered_df[filtered_df["Responsable"] == selected_responsible]
    if selected_status != "Tous":
        filtered_df = filtered_df[filtered_df["Statut"] == selected_status]

if not filtered_df.empty:
    # Afficher les tâches sous forme de cartes
    for _, task in filtered_df.iterrows():
        # Déterminer la classe CSS en fonction du statut
        status_class = ""
        if task["Statut"] == "Fini":
            status_class = "status-fini"
        elif task["Statut"] == "Pas fini":
            status_class = "status-pas-fini"
        elif task["Statut"] == "En cours":
            status_class = "status-en-cours"
        elif task["Statut"] == "Bloqué":
            status_class = "status-bloque"
            
        confirm_class = "confirmed" if task["Confirmé"] == "Oui" else "not-confirmed"
        
        with st.container():
            st.markdown(f'<div class="task-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{task['Tâche']}**")
                st.markdown(f"👤 **Responsable:** {task['Responsable']}")
            with col2:
                st.markdown(f"📅 **Date limite:** {task['Date limite']}")
            with col3:
                st.markdown(f'<span class="{status_class}">{task["Statut"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="{confirm_class}">Confirmé: {task["Confirmé"]}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Aucune tâche ne correspond aux filtres sélectionnés")

# --- Formulaire d'ajout de tâche ---
st.markdown('<h2 class="section-header">➕ Ajouter une nouvelle tâche</h2>', unsafe_allow_html=True)

with st.form("add_task", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        tache = st.text_input("Tâche *", placeholder="Entrez la description de la tâche")
        responsable = st.selectbox("Responsable *", ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"])
    with col2:
        date_limite = st.date_input("Date limite *", min_value=datetime.today().date())
        statut = st.selectbox("Statut *", ["Fini", "Pas fini", "En cours", "Bloqué"])
    
    confirme = st.checkbox("Confirmé ?")
    
    submitted = st.form_submit_button("Ajouter la tâche", type="primary")
    
    if submitted:
        if tache.strip() == "":
            st.error("Veuillez saisir une description de tâche")
        else:
            new_task = {
                "Tâche": tache,
                "Responsable": responsable,
                "Date limite": str(date_limite),
                "Statut": statut,
                "Confirmé": "Oui" if confirme else "Non"
            }
            df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
            save_data(df)
            st.success("✅ Tâche ajoutée avec succès !")
            st.rerun()

# --- Modification/Suppression de tâches ---
st.markdown('<h2 class="section-header">✏️ Modifier/Supprimer une tâche</h2>', unsafe_allow_html=True)

if not df.empty:
    task_to_edit = st.selectbox("Sélectionner une tâche à modifier/supprimer", df["Tâche"].tolist(), key="edit_select")
    
    if task_to_edit:
        task_index = df[df["Tâche"] == task_to_edit].index[0]
        task_data = df.loc[task_index]
        
        with st.form("edit_task"):
            col1, col2 = st.columns(2)
            with col1:
                edit_tache = st.text_input("Tâche", value=task_data["Tâche"], key="edit_tache")
                edit_responsable = st.selectbox("Responsable", ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"], 
                                              index=["Fedi", "Chayma", "Alaa", "Amen", "Wafa"].index(task_data["Responsable"]), key="edit_responsable")
            with col2:
                edit_date_limite = st.date_input("Date limite", 
                                                value=datetime.strptime(task_data["Date limite"], "%Y-%m-%d").date(), 
                                                key="edit_date")
                edit_statut = st.selectbox("Statut", ["Fini", "Pas fini", "En cours", "Bloqué"], 
                                         index=["Fini", "Pas fini", "En cours", "Bloqué"].index(task_data["Statut"]), key="edit_statut")
            
            edit_confirme = st.checkbox("Confirmé ?", value=task_data["Confirmé"] == "Oui", key="edit_confirm")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                update_clicked = st.form_submit_button("Mettre à jour", type="primary")
            with col2:
                delete_clicked = st.form_submit_button("Supprimer", type="secondary")
            
            if update_clicked:
                if edit_tache.strip() == "":
                    st.error("Veuillez saisir une description de tâche")
                else:
                    df.at[task_index, "Tâche"] = edit_tache
                    df.at[task_index, "Responsable"] = edit_responsable
                    df.at[task_index, "Date limite"] = str(edit_date_limite)
                    df.at[task_index, "Statut"] = edit_statut
                    df.at[task_index, "Confirmé"] = "Oui" if edit_confirme else "Non"
                    save_data(df)
                    st.success("✅ Tâche mise à jour avec succès !")
                    st.rerun()
            
            if delete_clicked:
                df = df.drop(task_index)
                save_data(df)
                st.warning(f"Tâche '{task_to_edit}' supprimée.")
                st.rerun()
else:
    st.info("Aucune tâche à modifier ou supprimer")
