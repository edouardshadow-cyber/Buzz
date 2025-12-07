import streamlit as st
import time # On utilise time.time() pour des calculs plus simples avec float

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Pro Buzzer 2.0", page_icon="🚨", layout="centered")

# --- URL DE L'IMAGE DU BUZZER ---
# Vous pouvez remplacer ce lien par le lien de votre propre image si vous le souhaitez.
BUZZER_IMAGE_URL = "https://cdn-icons-png.flaticon.com/512/3666/3666734.png"

# --- CSS PERSONNALISÉ ---
st.markdown(f"""
    <style>
    /* Style du GROS bouton buzzer central */
    /* On cible spécifiquement le bouton qui a une certaine clé ou structure */
    div[data-testid="stButton"] > button.buzzer-btn {
        width: 250px;
        height: 250px;
        border: none;
        background-color: transparent; /* Fond transparent */
        background-image: url('{BUZZER_IMAGE_URL}'); /* L'image du buzzer */
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        transition: transform 0.1s;
    }
    /* Effet quand on appuie dessus */
    div[data-testid="stButton"] > button.buzzer-btn:active {
         transform: scale(0.95);
         background-color: transparent; /* S'assurer qu'il reste transparent */
    }
     /* Retirer le focus rouge vilain sur mobile */
    div[data-testid="stButton"] > button.buzzer-btn:focus:not(:active) {
        border: none;
        color: transparent;
         background-color: transparent;
    }

    /* Style pour les statuts des joueurs */
    .player-status {
        font-size: 18px;
        margin: 3px;
        padding: 8px;
        border-radius: 8px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTION D'ÉTAT PARTAGÉ (MODIFIÉ POUR LE RELANCEMENT) ---
@st.cache_resource
class SharedGameState:
    def __init__(self):
        self.players = {}
        self.game_active = False
        self.buzzed_player = None
        self.final_buzzed_time = 0.0
        
        # Variables pour la gestion complexe du temps (pause/reprise)
        self.start_timestamp = None # Le moment exact où le segment actuel a commencé
        self.accumulated_time = 0.0 # Le temps total écoulé avant le dernier segment

    def add_player(self, name):
        if name and name not in self.players:
            self.players[name] = {'connected': False}

    def connect_player(self, name):
        if name in self.players:
            self.players[name]['connected'] = True

    # Lancement initial d'une nouvelle question
    def start_fresh_round(self):
        self.game_active = True
        self.buzzed_player = None
        self.accumulated_time = 0.0
        self.start_timestamp = time.time()

    # Relance après une mauvaise réponse (reprend le chrono où il était)
    def resume_round(self):
        self.game_active = True
        # On ne remet pas accumulated_time à 0 ici.
        # On redémarre juste un nouveau segment de temps maintenant.
        self.start_timestamp = time.time()
        self.buzzed_player = None

    def buzz(self, player_name):
        # On accepte le buzz seulement si le jeu est actif
        if self.game_active and self.buzzed_player is None:
            now = time.time()
            # Temps écoulé durant ce segment spécifique
            segment_duration = now - self.start_timestamp
            # Temps total = temps d'avant + temps de ce segment
            self.accumulated_time += segment_duration
            self.final_buzzed_time = self.accumulated_time

            self.buzzed_player = player_name
            self.game_active = False # On arrête le jeu
            return True
        return False

    def reset_game_totally(self):
        self.game_active = False
        self.buzzed_player = None
        self.accumulated_time = 0.0
        self.start_timestamp = None

game_state = SharedGameState()

# --- SON DE BUZZER ---
def play_buzzer_sound():
    sound_url = "https://www.myinstants.com/media/sounds/wrong-answer-sound-effect.mp3"
    st.markdown(f"""<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>""", unsafe_allow_html=True)

# --- BARRE LATÉRALE (ADMIN) ---
with st.sidebar:
    with st.popover("⚙️ Réglages Admin"):
        password = st.text_input("Mot de passe", type="password")
        if password == "admin":
            st.success("Mode Admin")
            
            st.subheader("1. Équipe")
            col_add1, col_add2 = st.columns([3, 1])
            new_member = col_add1.text_input("Nom", label_visibility="collapsed", placeholder="Nouveau nom...")
            if col_add2.button("Ajouter"):
                game_state.add_player(new_member)
                st.rerun()

            if st.button("⚠️ Vider toute l'équipe"):
                game_state.players = {}
                game_state.reset_game_totally()
                st.rerun()

            st.divider()
            st.subheader("2. Contrôle du Jeu")
            
            # Bouton GO principal
            if st.button("▶️ GO ! (Nouvelle question)", type="primary", use_container_width=True):
                game_state.start_fresh_round()
                st.rerun()

            # Bouton "Faux, relancer" qui n'apparaît que si quelqu'un a buzzé
            if game_state.buzzed_player:
                 st.warning("Réponse fausse ?")
                 if st.button("❌ Faux ! Relancer le chrono", use_container_width=True):
                     game_state.resume_round()
                     st.rerun()
            
            if st.button("⏹️ Reset la manche", use_container_width=True):
                game_state.reset_game_totally()
                st.rerun()
                    
        elif password:
            st.error("Mot de passe incorrect")

# --- LOGIN UTILISATEUR ---
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.current_user:
    st.title("👋 Bienvenue !")
    if not game_state.players:
        st.info("En attente que l'admin crée l'équipe...")
    else:
        options = ["-- Choisir son nom --"] + [p for p in game_state.players.keys() if not game_state.players[p]['connected']]
        choice = st.selectbox("", options)
        
        if st.button("Valider et entrer") and choice != "-- Choisir son nom --":
            st.session_state.current_user = choice
            game_state.connect_player(choice)
            st.rerun()

# --- INTERFACE PRINCIPALE (JEU) ---
else:
    current_user = st.session_state.current_user
    
    # Header avec la liste des joueurs
    cols_header = st.columns([1, 3])
    cols_header[0].markdown(f"### Moi: **{current_user}**")
    with cols_header[1]:
        st.caption("L'équipe :")
        cols_players = st.columns(4)
        for idx, (name, data) in enumerate(game_state.players.items()):
            icon = "🟢" if data['connected'] else "⚪"
            with cols_players[idx % 4]:
                 st.markdown(f"<div class='player-status'>{icon} {name}</div>", unsafe_allow_html=True)
    
    st.divider()

    # --- ZONE DE JEU (AUTO REFRESH RAPIDE) ---
    # Refresh rapide (0.3s) pour une bonne réactivité du chrono
    @st.fragment(run_every=0.3)
    def game_zone():
        # 1. État : Jeu en cours
        if game_state.game_active:
            st.markdown("<h2 style='text-align: center;'>Soyez prêts...</h2>", unsafe_allow_html=True)
            
            # Centrage du buzzer
            col_spacer1, col_buzzer, col_spacer2 = st.columns([1, 2, 1])
            with col_buzzer:
                # Notez l'ajout de key="buzzer_btn" pour le ciblage CSS
                # Le texte du bouton est vide car on utilise une image en background CSS
                if st.button("  ", key="buzzer-btn"):
                    game_state.buzz(current_user)
                    st.rerun()
            
            # Calcul du temps en direct
            if game_state.start_timestamp:
                current_segment_time = time.time() - game_state.start_timestamp
                total_time_live = game_state.accumulated_time + current_segment_time
                st.markdown(f"<h3 style='text-align: center; color: grey;'>⏱️ {total_time_live:.2f} s</h3>", unsafe_allow_html=True)

        # 2. État : Quelqu'un a buzzé
        elif game_state.buzzed_player:
            st.markdown("<h1 style='text-align: center; font-size: 80px;'>🚨 BUZZ !</h1>", unsafe_allow_html=True)
            
            # Affichage du nom en gros
            winner_color = "#28a745" if current_user == game_state.buzzed_player else "#dc3545"
            st.markdown(f"<h2 style='text-align: center; color: {winner_color}; font-size: 50px;'>{game_state.buzzed_player}</h2>", unsafe_allow_html=True)
            
            # Affichage du temps final arrêté
            st.markdown(f"<h3 style='text-align: center;'>Temps final : {game_state.final_buzzed_time:.2f} secondes</h3>", unsafe_allow_html=True)
            
            play_buzzer_sound()
            
            if current_user != game_state.buzzed_player:
                 st.info(f"{game_state.buzzed_player} est en train de répondre...")
            else:
                 st.success("À vous de répondre !")

        # 3. État : En attente
        else:
            st.markdown("<h3 style='text-align: center; color: grey; margin-top: 50px;'>⏳ En attente de l'animateur...</h3>", unsafe_allow_html=True)

    game_zone()
