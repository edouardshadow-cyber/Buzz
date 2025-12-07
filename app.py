import streamlit as st
import time
from datetime import datetime
import base64

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Team Buzzer", page_icon="🚨", layout="centered")

# --- CSS PERSONNALISÉ ---
# Pour faire un gros bouton rouge et styliser les icônes
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 150px;
        font-size: 50px;
        font-weight: bold;
        border-radius: 50%;
        border: 4px solid #8B0000;
        background-color: #FF0000;
        color: white;
        box-shadow: 0px 10px 15px rgba(0,0,0,0.3);
        transition: all 0.1s;
    }
    .stButton > button:active {
        background-color: #CC0000;
        transform: translateY(4px);
        box-shadow: 0px 5px 10px rgba(0,0,0,0.3);
    }
    .stButton > button:disabled {
        background-color: #555;
        border-color: #333;
        color: #888;
    }
    .player-status {
        font-size: 20px;
        margin: 5px;
        padding: 5px;
        border-radius: 10px;
        background-color: #f0f2f6;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTION D'ÉTAT PARTAGÉ (LE CŒUR DU SYSTÈME) ---
# Cette classe gère l'état du jeu pour TOUS les utilisateurs
@st.cache_resource
class SharedGameState:
    def __init__(self):
        self.players = {}  # Format: {'Nom': {'connected': False}}
        self.game_active = False
        self.buzzed_player = None
        self.buzzed_time = None
        self.start_time = None

    def add_player(self, name):
        if name and name not in self.players:
            self.players[name] = {'connected': False}

    def connect_player(self, name):
        if name in self.players:
            self.players[name]['connected'] = True

    def start_round(self):
        self.game_active = True
        self.buzzed_player = None
        self.buzzed_time = None
        self.start_time = datetime.now()

    def buzz(self, player_name):
        # On accepte le buzz seulement si personne n'a buzzé avant
        if self.game_active and self.buzzed_player is None:
            self.buzzed_player = player_name
            now = datetime.now()
            diff = now - self.start_time
            self.buzzed_time = diff.total_seconds()
            self.game_active = False # On arrête le jeu
            return True
        return False

    def reset_game(self):
        self.game_active = False
        self.buzzed_player = None
        self.buzzed_time = None

# Instanciation de l'état partagé
game_state = SharedGameState()

# --- SON DE BUZZER ---
def play_buzzer_sound():
    # Petit hack pour jouer un son HTML5
    sound_url = "https://www.myinstants.com/media/sounds/wrong-answer-sound-effect.mp3"
    st.markdown(f"""
        <audio autoplay>
            <source src="{sound_url}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)

# --- BARRE LATÉRALE (ADMIN) ---
with st.sidebar:
    with st.popover("⚙️ Réglages Admin"):
        password = st.text_input("Mot de passe", type="password")
        if password == "admin":
            st.success("Mode Admin Activé")
            
            st.markdown("### 1. Créer l'équipe")
            new_member = st.text_input("Nom du participant")
            if st.button("Ajouter membre"):
                game_state.add_player(new_member)
                st.success(f"{new_member} ajouté !")

            st.markdown("### 2. Contrôle du Jeu")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("GO ! (Lancer)", type="primary"):
                    game_state.start_round()
                    st.rerun()
            with col2:
                if st.button("Reset"):
                    game_state.reset_game()
                    st.rerun()
                    
            if st.button("Vider toute l'équipe (Reset Total)"):
                game_state.players = {}
                game_state.reset_game()
                st.rerun()
        elif password:
            st.error("Mot de passe incorrect")

# --- LOGIN UTILISATEUR ---
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.current_user:
    st.title("👋 Bienvenue !")
    if not game_state.players:
        st.warning("L'admin n'a pas encore créé l'équipe.")
    else:
        options = ["-- Choisir son nom --"] + [p for p in game_state.players.keys() if not game_state.players[p]['connected']]
        choice = st.selectbox("Qui êtes-vous ?", options)
        
        if st.button("Je suis là !") and choice != "-- Choisir son nom --":
            st.session_state.current_user = choice
            game_state.connect_player(choice)
            st.rerun()

# --- INTERFACE PRINCIPALE (JEU) ---
else:
    # L'utilisateur est connecté
    current_user = st.session_state.current_user
    
    # Header avec la liste des joueurs
    st.markdown("### 👥 L'Équipe")
    cols = st.columns(4)
    for idx, (name, data) in enumerate(game_state.players.items()):
        icon = "✅" if data['connected'] else "⏱️"
        # Distribution simple en colonnes
        with cols[idx % 4]:
            st.markdown(f"<div class='player-status'>{icon} {name}</div>", unsafe_allow_html=True)
    
    st.divider()

    # --- ZONE DE JEU (AUTO REFRESH) ---
    # On utilise st.fragment pour que cette partie se rafraichisse toute seule toutes les secondes
    # pour voir si l'admin a lancé le jeu ou si quelqu'un a buzzé.
    @st.fragment(run_every=0.5)
    def game_zone():
        # 1. État : Jeu en cours (On attend le buzz)
        if game_state.game_active:
            st.markdown(f"<h1 style='text-align: center;'>🔥 À VOUS DE JOUER {current_user.upper()} ! 🔥</h1>", unsafe_allow_html=True)
            
            # Le bouton Buzzer
            if st.button("BUZZ !!!"):
                success = game_state.buzz(current_user)
                if success:
                    st.rerun() # Force le refresh immédiat pour afficher le gagnant
            
            # Petit chronomètre visuel depuis le lancement
            if game_state.start_time:
                elapsed = datetime.now() - game_state.start_time
                st.caption(f"Temps écoulé : {elapsed.total_seconds():.1f}s")

        # 2. État : Quelqu'un a buzzé
        elif game_state.buzzed_player:
            st.markdown("<h1 style='text-align: center; font-size: 80px;'>🚨 BUZZ !</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; color: red;'>{game_state.buzzed_player}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>Temps : {game_state.buzzed_time:.2f} secondes</h3>", unsafe_allow_html=True)
            
            # Jouer le son (une seule fois pour éviter le spam audio à chaque refresh)
            # Note : le son se jouera sur tous les écrans connectés
            play_buzzer_sound()
            
            if current_user == game_state.buzzed_player:
                st.balloons()
            
            st.info("Attendez que l'admin relance une partie...")

        # 3. État : En attente de l'admin
        else:
            st.markdown("<h3 style='text-align: center; color: grey;'>⏳ En attente de l'admin...</h3>", unsafe_allow_html=True)

    game_zone()
