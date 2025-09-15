import streamlit as st
import pandas as pd
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
AIRTABLE_API_KEY = st.secrets.get("AIRTABLE_API_KEY", "votre_api_key")
AIRTABLE_BASE_ID = st.secrets.get("AIRTABLE_BASE_ID", "votre_base_id")
TABLE_NAME = "tasks"
URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# --- Fonctions Airtable ---
def create_task(task_data):
    try:
        data = {"records": [{"fields": task_data}]}
        response = requests.post(URL, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return True, "Tâche créée avec succès"
    except Exception as e:
        return False, f"Erreur lors de la création: {e}"

def update_task(task_id, task_data):
    try:
        data = {"records": [{"id": task_id, "fields": task_data}]}
        response = requests.patch(URL, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return True, "Tâche mise à jour avec succès"
    except Exception as e:
        return False, f"Erreur lors de la mise à jour: {e}"

def delete_task(task_id):
    try:
        delete_url = f"{URL}?records[]={task_id}"
        response = requests.delete(delete_url, headers=HEADERS)
        response.raise_for_status()
        return True, "Tâche supprimée avec succès"
    except Exception as e:
        return False, f"Erreur lors de la suppression: {e}"

# --- Charger les données depuis Airtable ---
@st.cache_data(ttl=300)
def load_data():
    try:
        response = requests.get(URL, headers=HEADERS)
        if response.status_code == 401:
            st.error("Erreur d'authentification Airtable.")
            return pd.DataFrame()
        if response.status_code == 404:
            st.error("Base Airtable non trouvée.")
            return pd.DataFrame()
        response.raise_for_status()
        data = response.json()
        records = data.get('records', [])
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
        if 'Date limite' in df.columns and not df.empty:
            df['Date limite'] = pd.to_datetime(df['Date limite']).dt.date
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return pd.DataFrame()

# --- Fonctions utilitaires ---
def get_status_icon(status):
    icons = {
        "À faire": "📋",
        "En cours": "🔄",
        "En revue": "👀",
        "Approuvé": "✅",
        "Rejeté": "❌",
        "Terminé": "🏁",
        "Archivé": "📁"
    }
    return icons.get(status, "📋")

def get_priority_class(priority):
    classes = {"Basse": "priority-basse", "Moyenne": "priority-moyenne", "Haute": "priority-haute"}
    return classes.get(priority, "priority-moyenne")

def get_urgency_badge(days_until_due):
    if days_until_due < 0:
        return "🔴 En retard"
    elif days_until_due <= 3:
        return "🔥 Urgent"
    elif days_until_due <= 7:
        return "⚠️ Bientôt"
    else:
        return ""

# --- Fonction pour créer une carte de tâche ---
def create_task_card(task, index, mobile=False):
    confirm_class = "✅ Oui" if task["Confirmé"] == "Oui" else "❌ Non"
    days_until_due = None
    urgency_badge = ""
    if "Date limite" in task and pd.notna(task["Date limite"]):
        days_until_due = (task["Date limite"] - datetime.today().date()).days
        urgency_badge = get_urgency_badge(days_until_due)
    progress_bar = ""
    if "Progression" in task and task["Progression"] > 0:
        progress_bar = f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {task['Progression']}%"></div>
        </div>
        <div class="progress-text">{task['Progression']}% complété</div>
        """
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

# --- Charger les données ---
df = load_data()

# --- CSS personnalisé ---
st.markdown("""
<style>
/* Ajoute ici ton CSS complet pour les cartes, Kanban, KPI, etc. */
</style>
""", unsafe_allow_html=True)

# --- Dashboard KPI ---
def render_dashboard(df):
    if not df.empty:
        today = datetime.today().date()
        total_tasks = len(df)
        completed_tasks = len(df[df["Statut"] == "Terminé"])
        overdue_tasks = len(df[(df["Date limite"] < today) & (df["Statut"] != "Terminé")])
        urgent_tasks = len(df[(df["Date limite"] >= today) & (df["Date limite"] <= today + pd.Timedelta(days=3)) & (df["Statut"] != "Terminé")])
        st.markdown(f"📋 Total tâches: {total_tasks} | ✅ Terminées: {completed_tasks} | ⏳ En retard: {overdue_tasks} | 🔥 Urgentes: {urgent_tasks}")

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;color:#1E3A8A;'>🌐 ANCU</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:gray;'>Gestion des tâches</p>", unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("⚙️ Configuration Airtable"):
        if st.button("🔄 Actualiser les données"):
            st.cache_data.clear()
            df = load_data()
            st.experimental_rerun()

    with st.expander("🎯 Filtres"):
        all_responsibles = ["Tous"] + sorted(df["Responsable"].unique().tolist()) if not df.empty else ["Tous"]
        selected_responsible = st.radio("👤 Responsable", all_responsibles)
        all_statuses = ["Tous"] + sorted(df["Statut"].unique().tolist()) if not df.empty else ["Tous"]
        selected_status = st.radio("📌 Statut", all_statuses)
        all_priorities = ["Tous"] + sorted(df["Priorité"].unique().tolist()) if not df.empty else ["Tous"]
        selected_priority = st.radio("🚨 Priorité", all_priorities)
        date_filter = st.select_slider("📅 Échéance", options=["Toutes", "Cette semaine", "Cette quinzaine", "Ce mois"], value="Toutes")

# --- Titre principal ---
st.markdown('<h1>✅ Gestion des Tâches ANCU</h1>', unsafe_allow_html=True)
st.info("📊 Données chargées depuis Airtable | Dernière actualisation: " + datetime.now().strftime("%H:%M:%S"))
render_dashboard(df)

# --- Filtrage des tâches ---
filtered_df = df.copy()
if not df.empty:
    if selected_responsible != "Tous":
        filtered_df = filtered_df[filtered_df["Responsable"] == selected_responsible]
    if selected_status != "Tous":
        filtered_df = filtered_df[filtered_df["Statut"] == selected_status]
    if selected_priority != "Tous":
        filtered_df = filtered_df[filtered_df["Priorité"] == selected_priority]
    
    today = datetime.today().date()
    if date_filter == "Cette semaine":
        filtered_df = filtered_df[filtered_df["Date limite"] <= today + pd.Timedelta(days=7)]
    elif date_filter == "Cette quinzaine":
        filtered_df = filtered_df[filtered_df["Date limite"] <= today + pd.Timedelta(days=14)]
    elif date_filter == "Ce mois":
        filtered_df = filtered_df[filtered_df["Date limite"] <= today + pd.Timedelta(days=30)]

# --- Affichage Kanban ---
statuses = ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"]
st.subheader("📋 Kanban des tâches")
if not filtered_df.empty:
    cols = st.columns(len(statuses))
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"### {get_status_icon(status)} {status}")
            tasks_status = filtered_df[filtered_df["Statut"] == status]
            for idx, task in tasks_status.iterrows():
                st.markdown(create_task_card(task, idx), unsafe_allow_html=True)
else:
    st.info("Aucune tâche ne correspond aux filtres sélectionnés")

# --- Formulaire d'ajout de tâche ---
st.subheader("➕ Ajouter une nouvelle tâche")
with st.form("add_task", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        tache = st.text_input("Tâche *")
        responsable = st.selectbox("Responsable *", ["Fedi", "Chayma", "Alaa", "Amen", "Wafa"])
        priorite = st.selectbox("Priorité *", ["Basse", "Moyenne", "Haute"])
    with col2:
        date_limite = st.date_input("Date limite *", min_value=datetime.today().date())
        statut = st.selectbox("Statut *", ["À faire", "En cours", "En revue", "Approuvé", "Rejeté", "Terminé", "Archivé"])
        progression = st.slider("Progression (%)", 0, 100, 0)
    commentaires = st.text_area("Commentaires / Journal de bord")
    confirme = st.checkbox("Confirmé ?")
    submitted = st.form_submit_button("Ajouter la tâche")
    
    if submitted:
        if tache.strip() == "":
            st.error("Veuillez saisir une description de tâche")
        else:
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
            success, message = create_task(new_task)
            if success:
                st.success(message)
                st.cache_data.clear()
                st.experimental_rerun()
            else:
                st.error(message)

# --- JavaScript pour actions des boutons ---
st.markdown("""
<script>
function editTask(index) { console.log("Modifier la tâche " + index); }
function deleteTask(index) { console.log("Supprimer la tâche " + index); }
</script>
""", unsafe_allow_html=True)
