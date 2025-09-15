# The provided code is already syntactically correct.
# No changes were needed to fix any syntax errors.

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import requests
import json
from streamlit_sortables import sort_items

# --- Configuration de la page ---
st.set_page_config(
    page_title="Gestion des Tâches ANCU",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Config Airtable ---
# Ces informations doivent être remplacées par vos véritables identifiants Airtable
AIRTABLE_API_KEY = st.secrets.get("AIRTABLE_API_KEY", "pat8pwKjxmpeyYdIC.9a8317c49467707c02a82d913172f4f05b64c894ef0b1edf880fb06147263397")
AIRTABLE_BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "appllTEXrUFuAaMaq")
TABLE_NAME = "tasks"
URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}", 
    "Content-Type": "application/json"
}

# --- Charger les données depuis Airtable ---
@st.cache_data(ttl=300)  # Cache pour 5 minutes
def load_data():
    try:
        response = requests.get(URL, headers=HEADERS)

        if response.status_code == 401:
            st.error("Erreur d'authentification Airtable. Vérifiez votre token API.")
            return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé", "Priorité", "Commentaires", "Progression"])
        
        if response.status_code == 404:
            st.error("Base Airtable non trouvée. Vérifiez votre Base ID.")
            return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé", "Priorité", "Commentaires", "Progression"])
        
        response.raise_for_status()  # Vérifie si la requête a réussi
        
        data = response.json()
        records = data.get('records', [])
        
        # Convertir les données Airtable en DataFrame
        tasks = []
        for record in records:
            fields = record.get('fields', {})
            task = {
                'id': record.get('id'),
                'Tâche': fields.get('Tâche', ''),
                'Responsable': ", ".join(fields.get('Responsable', [])) if isinstance(fields.get('Responsable', []), list) else fields.get('Responsable', ''),
                'Date limite': fields.get('Date limite', ''),
                'Statut': fields.get('Statut', ''),
                'Confirmé': fields.get('Confirmé', 'Non'),
                'Priorité': fields.get('Priorité', 'Moyenne'),
                'Commentaires': fields.get('Commentaires', ''),
                'Progression': fields.get('Progression', 0)
            }
            tasks.append(task)
        
        df = pd.DataFrame(tasks)
        
        # Convertir la date limite en datetime pour le filtrage
        if 'Date limite' in df.columns and not df.empty:
            df['Date limite'] = pd.to_datetime(df['Date limite']).dt.date
        
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à Airtable: {e}")
        return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé", "Priorité", "Commentaires", "Progression"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé", "Priorité", "Commentaires", "Progression"])

# --- Fonction pour créer une tâche dans Airtable ---
def create_task(task_data):
    try:
        data = {
            "records": [
                {
                    "fields": {
                        "Tâche": task_data["Tâche"],
                        "Responsable": task_data["Responsable"],
                        "Date limite": task_data["Date limite"],
                        "Statut": task_data["Statut"],
                        "Confirmé": task_data["Confirmé"],
                        "Priorité": task_data["Priorité"],
                        "Commentaires": task_data["Commentaires"],
                        "Progression": task_data["Progression"]
                    }
                }
            ]
        }
        
        response = requests.post(URL, headers=HEADERS, data=json.dumps(data))
        
        if response.status_code == 401:
            return False, "Erreur d'authentification. Vérifiez votre token API."
        
        response.raise_for_status()
        return True, "Tâche créée avec succès"
    except Exception as e:
        return False, f"Erreur lors de la création: {e}"

# --- Fonction pour mettre à jour une tâche dans Airtable ---
def update_task(task_id, task_data):
    try:
        data = {
            "records": [
                {
                    "id": task_id,
                    "fields": {
                        "Tâche": task_data["Tâche"],
                        "Responsable": task_data["Responsable"],
                        "Date limite": task_data["Date limite"],
                        "Statut": task_data["Statut"],
                        "Confirmé": task_data["Confirmé"],
                        "Priorité": task_data["Priorité"],
                        "Commentaires": task_data["Commentaires"],
                        "Progression": task_data["Progression"]
                    }
                }
            ]
        }
        
        response = requests.patch(URL, headers=HEADERS, data=json.dumps(data))
        
        if response.status_code == 401:
            return False, "Erreur d'authentification. Vérifiez votre token API."
        
        response.raise_for_status()
        return True, "Tâche mise à jour avec succès"
    except Exception as e:
        return False, f"Erreur lors de la mise à jour: {e}"

# --- Fonction pour supprimer une tâche dans Airtable ---
def delete_task(task_id):
    try:
        delete_url = f"{URL}?records[]={task_id}"
        response = requests.delete(delete_url, headers=HEADERS)
        
        if response.status_code == 401:
            return False, "Erreur d'authentification. Vérifiez votre token API."
        
        response.raise_for_status()
        return True, "Tâche supprimée avec succès"
    except Exception as e:
        return False, f"Erreur lors de la suppression: {e}"

# Fonction pour obtenir la classe CSS selon le statut
def get_status_class(status):
    status_classes = {
        "À faire": "status-a-faire",
        "En cours": "status-en-cours",
        "En revue": "status-en-revue",
        "Approuvé": "status-approuve",
        "Rejeté": "status-rejete",
        "Terminé": "status-termine",
        "Archivé": "status-archive"
    }
    return status_classes.get(status, "status-a-faire")

# Fonction pour obtenir la classe CSS selon la priorité
def get_priority_class(priority):
    priority_classes = {
        "Basse": "priority-basse",
        "Moyenne": "priority-moyenne",
        "Haute": "priority-haute"
    }
    return priority_classes.get(priority, "priority-moyenne")

# Fonction pour obtenir le badge d'urgence selon les jours restants
def get_urgency_badge(days_until_due):
    if days_until_due < 0:
        return "🔴 En retard"
    elif days_until_due <= 3:
        return "🔥 Urgent"
    elif days_until_due <= 7:
        return "⚠️ Bientôt"
    else:
        return ""

# Fonction pour obtenir l'icône selon le statut
def get_status_icon(status):
    status_icons = {
        "À faire": "📋",
        "En cours": "🔄",
        "En revue": "👀",
        "Approuvé": "✅",
        "Rejeté": "❌",
        "Terminé": "🏁",
        "Archivé": "📁"
    }
    return status_icons.get(status, "📋")

# Charger les données
df = load_data()

# --- CSS personnalisé responsive ---
st.markdown("""
<style>
    /* Conteneur principal : responsive */
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
        }
    }

    .section-header {
        color: #1E3A8A;
        border-bottom: 2px solid #1E3A8A;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        font-size: 1.4rem;
    }
    @media (max-width: 768px) {
        .section-header {
            font-size: 1.1rem;
        }
    }

    /* Dashboard KPI */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    @media (max-width: 768px) {
        .kpi-container {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    .kpi-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #6B7280;
    }

    /* Grille de tâches responsive */
    .tasks-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    @media (max-width: 480px) {
        .tasks-grid {
            grid-template-columns: 1fr;
        }
    }

    /* Carte de tâche */
    .task-card {
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        min-height: 200px;
        margin-bottom: 1rem;
        cursor: grab;
    }
    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    /* Titre tâche */
    .task-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        color: #1E3A8A;
        line-height: 1.3;
    }
    @media (max-width: 768px) {
        .task-title {
            font-size: 1rem;
        }
    }

    /* Détails */
    .task-detail {
        font-size: 0.9rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }
    .task-detail-icon {
        margin-right: 0.5rem;
        opacity: 0.7;
        width: 20px;
        text-align: center;
    }

    /* Barre de progression */
    .progress-container {
        width: 100%;
        background-color: #E5E7EB;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .progress-bar {
        height: 8px;
        border-radius: 0.5rem;
        background-color: #10B981;
        text-align: center;
        line-height: 8px;
        color: white;
        font-size: 0.7rem;
    }
    .progress-text {
        font-size: 0.8rem;
        text-align: right;
        margin-top: 0.2rem;
    }

    /* Statuts (badges responsives) */
    .task-status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0.8rem 0;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .status-a-faire, .status-en-cours, .status-en-revue,
    .status-approuve, .status-rejete, .status-termine, .status-archive {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }

    .status-a-faire { background-color: #E5E7EB; color: #374151; }
    .status-en-cours { background-color: #FEF3C7; color: #92400E; }
    .status-en-revue { background-color: #DBEAFE; color: #1E40AF; }
    .status-approuve, .status-termine { background-color: #D1FAE5; color: #065F46; }
    .status-rejete { background-color: #FEE2E2; color: #991B1B; }
    .status-archive { background-color: #E5E7EB; color: #374151; }

    /* Priorités */
    .priority-basse, .priority-moyenne, .priority-haute {
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .priority-basse { background-color: #D1FAE5; color: #065F46; }
    .priority-moyenne { background-color: #FEF3C7; color: #92400E; }
    .priority-haute { background-color: #FEE2E2; color: #991B1B; }

    /* Badges d'urgence */
    .urgency-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
        margin-left: 0.5rem;
    }
    .urgency-urgent { background-color: #FEE2E2; color: #DC2626; }
    .urgency-warning { background-color: #FEF3C7; color: #D97706; }
    .urgency-normal { background-color: #D1FAE5; color: #059669; }

    /* Confirmé / Non confirmé */
    .confirmed { color: #065F46; font-weight: 600; font-size: 0.8rem; }
    .not-confirmed { color: #991B1B; font-weight: 600; font-size: 0.8rem; }

    /* Jours restants */
    .days-remaining {
        font-weight: 600;
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 0.5rem;
        display: inline-block;
    }
    .days-remaining.urgent { background-color: #FEE2E2; color: #DC2626; }
    .days-remaining.warning { background-color: #FEF3C7; color: #D97706; }
    .days-remaining.normal { background-color: #D1FAE5; color: #059669; }

    /* Boutons actions flexibles */
    .task-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: auto;
        padding-top: 0.8rem;
        flex-wrap: wrap;
    }
    .task-actions button {
        flex: 1 1 auto;
        padding: 0.4rem;
        font-size: 0.8rem;
        min-width: 90px;
    }

    /* Indicateurs de priorité */
    .urgent { border-left: 4px solid #DC2626; }
    .due-soon { border-left: 4px solid #F59E0B; }
    .on-track { border-left: 4px solid #10B981; }

     /* Empêcher la coupure des mots */
    .task-title, .task-detail, .status-a-faire, .status-en-cours, 
    .status-en-revue, .status-approuve, .status-rejete, 
    .status-termine, .status-archive {
        white-space: nowrap;         /* Pas de retour auto */
        overflow: hidden;            /* Cache ce qui dépasse */
        text-overflow: ellipsis;     /* Ajoute "..." si trop long */
    }

    /* Adapter la largeur du contenu quand la sidebar est ouverte */
    .block-container {
        max-width: 100% !important;  /* Utiliser toute la largeur */
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Permettre le scroll horizontal si trop serré */
    .main, .block-container {
        overflow-x: auto;
    }

    /* Pour les colonnes du Kanban : scroll horizontal sur petit écran */
    @media (max-width: 1024px) {
        .element-container:has(.stColumns) {
            overflow-x: auto;
            display: flex;
            gap: 1rem;
        }
        .element-container:has(.stColumns) > div {
            min-width: 250px; /* largeur mini de chaque colonne */
        }
    }

    /* Style pour les colonnes du Kanban */
    .kanban-column {
        background-color: #F9FAFB;
        border-radius: 0.5rem;
        padding: 1rem;
        min-height: 500px;
    }
    .kanban-header {
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E5E7EB;
    }

    /* Style pour mobile - accordéon */
    @media (max-width: 768px) {
        .kanban-accordion {
            margin-bottom: 1rem;
        }
        .kanban-accordion .task-card {
            margin-bottom: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Dashboard KPI ---
def render_dashboard():
    if not df.empty:
        today = datetime.today().date()
        
        total_tasks = len(df)
        completed_tasks = len(df[df["Statut"] == "Terminé"]) if "Statut" in df.columns else 0
        overdue_tasks = len(df[(df["Date limite"] < today) & (df["Statut"] != "Terminé")]) if "Date limite" in df.columns else 0
        urgent_tasks = len(df[(df["Date limite"] >= today) & 
                             (df["Date limite"] <= today + pd.Timedelta(days=3)) & 
                             (df["Statut"] != "Terminé")]) if "Date limite" in df.columns else 0
        
        st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">📋 Total tâches</div><div class="kpi-value">{total_tasks}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">✅ Terminées</div><div class="kpi-value">{completed_tasks}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">⏳ En retard</div><div class="kpi-value">{overdue_tasks}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🔥 Urgentes</div><div class="kpi-value">{urgent_tasks}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- Configuration Airtable dans la sidebar ---
with st.sidebar:
    # --- En-tête ---
    st.markdown("<h1 style='text-align: center; color:#1E3A8A;'>🌐 ANCU</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size:0.9rem; color:gray;'>Gestion des tâches</p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Section Configuration ---
    with st.expander("⚙️ Configuration Airtable", expanded=False):
        if st.button("🔄 Actualiser les données"):
            st.cache_data.clear()
            df = load_data()
            st.rerun()

    # --- Section Filtres (compact mode) ---
    with st.expander("🎯 Filtres", expanded=True):
        # Responsable avec radio (compact)
        all_responsibles = ["Tous"] + sorted(df["Responsable"].unique().tolist()) if not df.empty and "Responsable" in df.columns else ["Tous"]
        selected_responsible = st.radio("👤 Responsable", all_responsibles, horizontal=False)

        # Statut avec radio (compact)
        all_statuses = ["Tous"] + sorted(df["Statut"].unique().tolist()) if not df.empty and "Statut" in df.columns else ["Tous"]
        selected_status = st.radio("📌 Statut", all_statuses, horizontal=False)
        
        # Priorité avec radio (compact)
        all_priorities = ["Tous"] + sorted(df["Priorité"].unique().tolist()) if not df.empty and "Priorité" in df.columns else ["Tous"]
        selected_priority = st.radio("🚨 Priorité", all_priorities, horizontal=False)

        # Filtre de date avec select_slider (compact + visuel)
        date_filter = st.select_slider("📅 Échéance", options=["Toutes", "Cette semaine", "Cette quinzaine", "Ce mois"], value="Toutes")

    # --- Section Statistiques avec badges et progress bar ---
    with st.expander("📊 Statistiques", expanded=True):
        if not df.empty:
            total_tasks = len(df)
            completed_tasks = len(df[df["Statut"] == "Terminé"]) if "Statut" in df.columns else 0
            confirmed_tasks = len(df[df["Confirmé"] == "Oui"]) if "Confirmé" in df.columns else 0

            # --- Badges dynamiques ---
            today = datetime.today().date()
            urgent_tasks = len(df[(df["Date limite"] < today) & (df["Statut"] != "Terminé")])
            due_soon_tasks = len(df[(df["Date limite"] >= today) & 
                                    (df["Date limite"] <= today + pd.Timedelta(days=3)) & 
                                    (df["Statut"] != "Terminé")])
            high_priority_tasks = len(df[(df["Priorité"] == "Haute") & (df["Statut"] != "Terminé")])

            st.markdown(f"🔴 **Urgentes** : {urgent_tasks}")
            st.markdown(f"🟡 **À échéance proche** : {due_soon_tasks}")
            st.markdown(f"⚡ **Haute priorité** : {high_priority_tasks}")
            st.markdown(f"🟢 **Terminées** : {completed_tasks}")

            # --- Progress bar de complétion ---
            completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
            st.progress(completion_rate / 100)
            st.caption(f"Taux de complétion : {completion_rate}%")

            # --- Autre info ---
            st.metric("🔒 Tâches confirmées", f"{confirmed_tasks}/{total_tasks}")
        else:
            st.info("Aucune tâche à afficher")

# --- Titre principal ---
st.markdown('<h1 class="main-header">✅ Gestion des Tâches ANCU</h1>', unsafe_allow_html=True)

# Information sur la source des données
st.info("📊 Données chargées depuis Airtable | Dernière actualisation: " + datetime.now().strftime("%H:%M:%S"))

# --- Dashboard KPI ---
render_dashboard()

# --- Tableau des tâches avec filtres ---
st.markdown('<h2 class="section-header">📋 Liste des tâches</h2>', unsafe_allow_html=True)

# Appliquer les filtres
filtered_df = df.copy()
if not df.empty:
    if selected_responsible != "Tous" and "Responsable" in df.columns:
        filtered_df = filtered_df[filtered_df["Responsable"] == selected_responsible]
    if selected_status != "Tous" and "Statut" in df.columns:
        filtered_df = filtered_df[filtered_df["Statut"] == selected_status]
    if selected_priority != "Tous" and "Priorité" in df.columns:
        filtered_df = filtered_df[filtered_df["Priorité"] == selected_priority]
    
    # Filtrer par date
    today = datetime.today().date()
    if date_filter == "Cette semaine" and "Date limite" in df.columns:
        next_week = today + pd.Timedelta(days=7)
        filtered_df = filtered_df[filtered_df["Date limite"] <= next_week]
    elif date_filter == "Cette quinzaine" and "Date limite" in df.columns:
        next_two_weeks = today + pd.Timedelta(days=14)
        filtered_df = filtered_df[filtered_df["Date limite"] <= next_two_weeks]
    elif date_filter == "Ce mois" and "Date limite" in df.columns:
        next_month = today + pd.Timedelta(days=30)
        filtered_df = filtered_df[filtered_df["Date limite"] <= next_month]

if not filtered_df.empty:
    st.subheader("Kanban des tâches")

    statuses = ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"]
    
    # Vérifier si on est sur mobile
    is_mobile = st.session_state.get('is_mobile', False)
    
    if not is_mobile:
        # Mode desktop - colonnes horizontales
        cols = st.columns(len(statuses))
        
        for i, status in enumerate(statuses):
            with cols[i]:
                st.markdown(f'<div class="kanban-header">{get_status_icon(status)} {status}</div>', unsafe_allow_html=True)
                tasks_status = filtered_df[filtered_df["Statut"] == status]
                
                if not tasks_status.empty:
                    task_items = []
                    for index, task in tasks_status.iterrows():
                        # Créer le contenu de la carte
                        task_content = create_task_card(task, index)
                        task_items.append(task_content)
                    
                    # Utiliser le drag and drop
                    sorted_items = sort_items(task_items, direction="vertical")
                    
                    # Mettre à jour les statuts si des tâches ont été déplacées
                    for item in sorted_items:
                        if "data-id" in item:
                            task_id = item["data-id"]
                            new_status = status
                            # Trouver la tâche et mettre à jour son statut
                            task_index = next((i for i, t in tasks_status.iterrows() if str(t['id']) == task_id), None)
                            if task_index is not None:
                                if df.loc[task_index, 'Statut'] != new_status:
                                    df.loc[task_index, 'Statut'] = new_status
                                    # Mettre à jour dans Airtable
                                    task_data = {
                                        "Tâche": df.loc[task_index, 'Tâche'],
                                        "Responsable": df.loc[task_index, 'Responsable'],
                                        "Date limite": str(df.loc[task_index, 'Date limite']),
                                        "Statut": new_status,
                                        "Confirmé": df.loc[task_index, 'Confirmé'],
                                        "Priorité": df.loc[task_index, 'Priorité'],
                                        "Commentaires": df.loc[task_index, 'Commentaires'],
                                        "Progression": df.loc[task_index, 'Progression']
                                    }
                                    success, message = update_task(task_id, task_data)
                                    if success:
                                        st.success(f"Tâche déplacée vers {new_status}")
                                        st.cache_data.clear()
                                        time.sleep(1)
                                        st.rerun()
                else:
                    st.info("Aucune tâche")
    else:
        # Mode mobile - accordéon
        for status in statuses:
            with st.expander(f"{get_status_icon(status)} {status}", expanded=False):
                tasks_status = filtered_df[filtered_df["Statut"] == status]
                
                if not tasks_status.empty:
                    for index, task in tasks_status.iterrows():
                        # Créer le contenu de la carte
                        task_content = create_task_card(task, index, mobile=True)
                        st.markdown(task_content, unsafe_allow_html=True)
                else:
                    st.info("Aucune tâche")
else:
    st.info("Aucune tâche ne correspond aux filtres sélectionnés")

# --- Fonction pour créer une carte de tâche ---
def create_task_card(task, index, mobile=False):
    # Déterminer confirmation
    confirm_class = "✅ Oui" if task["Confirmé"] == "Oui" else "❌ Non"

    # Calcul jours restants et badge d'urgence
    days_until_due = None
    urgency_badge = ""
    if "Date limite" in task and pd.notna(task["Date limite"]):
        days_until_due = (task["Date limite"] - datetime.today().date()).days
        urgency_badge = get_urgency_badge(days_until_due)
    
    # Barre de progression
    progress_bar = ""
    if "Progression" in task and task["Progression"] > 0:
        progress_bar = f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {task['Progression']}%"></div>
        </div>
        <div class="progress-text">{task['Progression']}% complété</div>
        """
    
    # Créer la carte
    card_content = f"""
    <div class="task-card" data-id="{task['id']}">
        <div class="task-title">{task['Tâche']} {urgency_badge}</div>
        <div class="task-detail"><span class="task-detail-icon">👤</span> {task['Responsable']}</div>
        <div class="task-detail"><span class="task-detail-icon">🚨</span> <span class="{get_priority_class(task['Priorité'])}">{task['Priorité']}</span></div>
        {"<div class='task-detail'><span class='task-detail-icon'>📅</span> " + str(task['Date limite']) + f" (<span class='days-remaining {'urgent' if days_until_due <= 3 else 'warning' if days_until_due <= 7 else 'normal'}'>{days_until_due} jours restants</span>)</div>" if pd.notna(task['Date limite']) else ""}
        <div class="task-detail"><span class="task-detail-icon">✅</span> {confirm_class}</div>
        {progress_bar}
        {"<div class='task-detail'><span class='task-detail-icon'>💬</span> " + task['Commentaires'] + "</div>" if task['Commentaires'] else ""}
        <div class="task-actions">
            <button onclick="editTask('{index}')">✏️ Modifier</button>
            <button onclick="deleteTask('{index}')">🗑️ Supprimer</button>
        </div>
    </div>
    """
    
    return card_content

# --- Formulaire d'ajout de tâche ---
st.markdown('<h2 class="section-header">➕ Ajouter une nouvelle tâche</h2>', unsafe_allow_html=True)

with st.form("add_task", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        tache = st.text_input("Tâche *", placeholder="Entrez la description de la tâche")
        responsable = st.selectbox("Responsable *", ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"])
        priorite = st.selectbox("Priorité *", ["Basse", "Moyenne", "Haute"])
    with col2:
        date_limite = st.date_input("Date limite *", min_value=datetime.today().date())
        statut = st.selectbox("Statut *", ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"])
        progression = st.slider("Progression (%)", 0, 100, 0)
    
    commentaires = st.text_area("Commentaires / Journal de bord")
    confirme = st.checkbox("Confirmé ?")
    
    submitted = st.form_submit_button("Ajouter la tâche", type="primary")
    
    if submitted:
        if tache.strip() == "":
            st.error("Veuillez saisir une description de tâche")
        else:
            # Afficher un loader
            with st.spinner("Ajout en cours..."):
                time.sleep(1)  # Simuler un traitement
                
                # Préparer les données pour Airtable
                new_task = {
                    "Tâche": tache,
                    "Responsable": responsable,
                    "Priorité": priorite,
                    "Date limite": str(date_limite),
                    "Statut": statut,
                    "Commentaires": commentaires,
                    "Progression": progression,
                    "Confirmé": "Oui" if confirme else "Non"
                }
                
                # Créer dans Airtable
                success, message = create_task(new_task)
                
                if success:
                    st.success("✅ " + message)
                    st.cache_data.clear()  # Effacer le cache pour recharger les données
                    time.sleep(1)  # Petit délai pour voir le message
                    st.rerun()
                else:
                    st.error("❌ " + message)

# --- JavaScript pour les actions des boutons ---
st.markdown("""
<script>
function editTask(index) {
    // Cette fonction sera implémentée pour ouvrir le modal d'édition
    console.log("Modifier la tâche " + index);
}

function deleteTask(index) {
    // Cette fonction sera implémentée pour ouvrir le modal de suppression
    console.log("Supprimer la tâche " + index);
}
</script>
""", unsafe_allow_html=True)
