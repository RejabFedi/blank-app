import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import requests
import json

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
            return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé"])
        
        if response.status_code == 404:
            st.error("Base Airtable non trouvée. Vérifiez votre Base ID.")
            return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé"])
        
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
                'Confirmé': fields.get('Confirmé', 'Non')
            }
            tasks.append(task)
        
        df = pd.DataFrame(tasks)
        
        # Convertir la date limite en datetime pour le filtrage
        if 'Date limite' in df.columns and not df.empty:
            df['Date limite'] = pd.to_datetime(df['Date limite']).dt.date
        
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à Airtable: {e}")
        return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return pd.DataFrame(columns=["id", "Tâche", "Responsable", "Date limite", "Statut", "Confirmé"])

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
                        "Confirmé": task_data["Confirmé"]
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
                        "Confirmé": task_data["Confirmé"]
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

# Charger les données
df = load_data()

# --- CSS personnalisé ---
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
</style>
""", unsafe_allow_html=True)



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

        # Filtre de date avec select_slider (compact + visuel)
        date_filter = st.select_slider("📅 Échéance", options=["Toutes", "Cette semaine", "Cette quinzaine", "Ce mois"], value="Toutes")

    # --- Section Statistiques avec badges et progress bar ---
    with st.expander("📊 Statistiques", expanded=True):
        if not df.empty:
            total_tasks = len(df)
            completed_tasks = len(df[df["Statut"] == "Terminé"]) if "Statut" in df.columns else 0
            confirmed_tasks = len(df[df["Confirmé"] == "Oui"]) if "Confirmé" in df.columns else 0

            # --- Badges dynamiques ---
            urgent_tasks = len(df[(df["Date limite"] < datetime.today().date()) & (df["Statut"] != "Terminé")])
            due_soon_tasks = len(df[(df["Date limite"] >= datetime.today().date()) & 
                                    (df["Date limite"] <= datetime.today().date() + pd.Timedelta(days=3)) & 
                                    (df["Statut"] != "Terminé")])

            st.markdown(f"🔴 **Urgentes** : {urgent_tasks}")
            st.markdown(f"🟡 **À échéance proche** : {due_soon_tasks}")
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

# --- Tableau des tâches avec filtres ---
st.markdown('<h2 class="section-header">📋 Liste des tâches</h2>', unsafe_allow_html=True)



# Appliquer les filtres
filtered_df = df.copy()
if not df.empty:
    if selected_responsible != "Tous" and "Responsable" in df.columns:
        filtered_df = filtered_df[filtered_df["Responsable"] == selected_responsible]
    if selected_status != "Tous" and "Statut" in df.columns:
        filtered_df = filtered_df[filtered_df["Statut"] == selected_status]
    
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
    cols = st.columns(len(statuses))

    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"### {status}")
            tasks_status = filtered_df[filtered_df["Statut"] == status]

            if not tasks_status.empty:
                for index, task in tasks_status.iterrows():
                    # Déterminer confirmation
                    confirm_class = "✅ Oui" if task["Confirmé"] == "Oui" else "❌ Non"

                    # Calcul jours restants
                    days_until_due = "N/A"
                    if "Date limite" in task and pd.notna(task["Date limite"]):
                        days_until_due = (task["Date limite"] - today).days

                    # Bloc d'affichage (expander par tâche)
                    with st.expander(f"{task['Tâche']}"):
                        st.write(f"👤 Responsable : {task['Responsable']}")
                        if pd.notna(task["Date limite"]):
                            st.write(f"📅 Échéance : {task['Date limite']} ({days_until_due} jours restants)")
                        st.write(f"✅ Confirmé : {confirm_class}")

                        # Boutons d'action
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✏️ Modifier", key=f"edit_{index}"):
                                st.session_state[f"edit_index_{index}"] = True
                        with col2:
                            if st.button(f"🗑️ Supprimer", key=f"delete_{index}"):
                                st.session_state[f"delete_index_{index}"] = True

                        # --- Modal de modification ---
                        if f"edit_index_{index}" in st.session_state and st.session_state[f"edit_index_{index}"]:
                            with st.form(f"edit_form_{index}"):
                                st.subheader("Modifier la tâche")

                                edit_tache = st.text_input("Tâche", value=task["Tâche"], key=f"edit_tache_{index}")
                                edit_responsable = st.selectbox("Responsable", ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"],
                                    index=["Fedi", "Chayma", "Alaa", "Amen", "Wafa"].index(task["Responsable"]) if task["Responsable"] in ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"] else 0,
                                    key=f"edit_responsable_{index}")

                                current_date = task["Date limite"] if "Date limite" in task and pd.notna(task["Date limite"]) else datetime.today().date()
                                edit_date_limite = st.date_input("Date limite", value=current_date, key=f"edit_date_{index}")

                                edit_statut = st.selectbox("Statut", ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"],
                                    index=["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"].index(task["Statut"]) 
                                    if task["Statut"] in ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"] else 0,
                                    key=f"edit_statut_{index}")

                                edit_confirme = st.checkbox("Confirmé ?", value=task["Confirmé"] == "Oui", key=f"edit_confirm_{index}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("Confirmer la modification", type="primary"):
                                        if edit_tache.strip() == "":
                                            st.error("Veuillez saisir une description de tâche")
                                        else:
                                            with st.spinner("Modification en cours..."):
                                                time.sleep(1)
                                                updated_task = {
                                                    "Tâche": edit_tache,
                                                    "Responsable": edit_responsable,
                                                    "Date limite": str(edit_date_limite),
                                                    "Statut": edit_statut,
                                                    "Confirmé": "Oui" if edit_confirme else "Non"
                                                }
                                                success, message = update_task(task['id'], updated_task)
                                                if success:
                                                    st.success("✅ " + message)
                                                    st.session_state[f"edit_index_{index}"] = False
                                                    st.cache_data.clear()
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error("❌ " + message)
                                with col2:
                                    if st.form_submit_button("Annuler"):
                                        st.session_state[f"edit_index_{index}"] = False
                                        st.rerun()

                        # --- Modal de suppression ---
                        if f"delete_index_{index}" in st.session_state and st.session_state[f"delete_index_{index}"]:
                            st.subheader("Confirmer la suppression")
                            st.warning(f"Êtes-vous sûr de vouloir supprimer la tâche : '{task['Tâche']}' ? Cette action est irréversible.")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Oui, supprimer", type="primary", key=f"confirm_delete_{index}"):
                                    with st.spinner("Suppression en cours..."):
                                        time.sleep(1)
                                        success, message = delete_task(task['id'])
                                        if success:
                                            st.success("✅ " + message)
                                            st.session_state[f"delete_index_{index}"] = False
                                            st.cache_data.clear()
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ " + message)
                            with col2:
                                if st.button("Annuler", key=f"cancel_delete_{index}"):
                                    st.session_state[f"delete_index_{index}"] = False
                                    st.rerun()
            else:
                st.info("Aucune tâche")
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
        statut = st.selectbox("Statut *", ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"])
    
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
                    "Date limite": str(date_limite),
                    "Statut": statut,
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
