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
    .tasks-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .task-card {
        padding: 1.2rem;
        border-radius: 0.8rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 0;
        background-color: white;
        position: relative;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .task-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
    .task-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        line-height: 1.3;
        color: #1E3A8A;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .task-detail {
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
    }
    .task-detail-icon {
        margin-right: 0.5rem;
        opacity: 0.7;
    }
    .task-status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.8rem;
    }
    .status-fini {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.3rem 0.6rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-pas-fini {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.3rem 0.6rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-en-cours {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.3rem 0.6rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-bloque {
        background-color: #E5E7EB;
        color: #374151;
        padding: 0.3rem 0.6rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .confirmed {
        color: #065F46;
        font-weight: 600;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
    }
    .not-confirmed {
        color: #991B1B;
        font-weight: 600;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
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
    .urgent {
        border-left: 5px solid #DC2626;
    }
    .due-soon {
        border-left: 5px solid #F59E0B;
    }
    .on-track {
        border-left: 5px solid #10B981;
    }
    .action-buttons {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .days-remaining {
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.2rem 0.5rem;
        border-radius: 0.8rem;
        background-color: #F3F4F6;
    }
    .days-remaining.urgent {
        background-color: #FEE2E2;
        color: #DC2626;
    }
    .days-remaining.warning {
        background-color: #FEF3C7;
        color: #D97706;
    }
    .days-remaining.normal {
        background-color: #D1FAE5;
        color: #059669;
    }
</style>
""", unsafe_allow_html=True)

# ... (le reste du code reste inchangé jusqu'à la section d'affichage des tâches)

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
    # Afficher les tâches sous forme de grille de cartes
    st.markdown('<div class="tasks-grid">', unsafe_allow_html=True)
    
    for index, task in filtered_df.iterrows():
        # Déterminer la classe CSS en fonction du statut et de la date
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
        
        # Déterminer la priorité basée sur la date
        date_class = "on-track"
        days_class = "normal"
        days_until_due = "N/A"
        
        if "Date limite" in task and pd.notna(task["Date limite"]):
            days_until_due = (task["Date limite"] - today).days
            if days_until_due <= 2:
                date_class = "urgent"
                days_class = "urgent"
            elif days_until_due <= 7:
                date_class = "due-soon"
                days_class = "warning"
        else:
            days_until_due = "N/A"
        
        # Afficher chaque tâche dans une carte
        with st.container():
            st.markdown(f'<div class="task-card {date_class}">', unsafe_allow_html=True)
            
            # Titre de la tâche
            st.markdown(f'<div class="task-title">{task["Tâche"]}</div>', unsafe_allow_html=True)
            
            # Détails de la tâche
            st.markdown(f'''
                <div class="task-detail">
                    <span class="task-detail-icon">👤</span>
                    <span>{task["Responsable"]}</span>
                </div>
            ''', unsafe_allow_html=True)
            
            if "Date limite" in task and pd.notna(task["Date limite"]):
                st.markdown(f'''
                    <div class="task-detail">
                        <span class="task-detail-icon">📅</span>
                        <span>{task["Date limite"]}</span>
                    </div>
                ''', unsafe_allow_html=True)
            
            # Ligne de statut et jours restants
            st.markdown('<div class="task-status-row">', unsafe_allow_html=True)
            st.markdown(f'<span class="{status_class}">{task["Statut"]}</span>', unsafe_allow_html=True)
            
            if days_until_due != "N/A":
                st.markdown(f'<span class="days-remaining {days_class}">{days_until_due} jours</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Confirmation
            st.markdown(f'<div class="task-detail"><span class="{confirm_class}">Confirmé: {task["Confirmé"]}</span></div>', unsafe_allow_html=True)
            
            # Boutons d'action
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✏️ Modifier", key=f"edit_{index}"):
                    st.session_state[f"edit_index_{index}"] = True
            with col2:
                if st.button(f"🗑️ Supprimer", key=f"delete_{index}"):
                    st.session_state[f"delete_index_{index}"] = True
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Modals d'édition et suppression (le code reste inchangé)
            # ... (garder le code existant pour les modals d'édition et suppression)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fermer la grille
else:
    st.info("Aucune tâche ne correspond aux filtres sélectionnés")

# ... (le reste du code reste inchangé)

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
