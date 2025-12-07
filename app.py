import streamlit as st
import time
import qrcode
from io import BytesIO

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Team Buzzer", page_icon="🚨", layout="centered")

# --- URL DE VOTRE APP ---
APP_URL = "https://jmgdqtj4u9obietzmgj2hg.streamlit.app/"

# --- CSS ET STYLE (CRUCIAL POUR L'AFFICHAGE) ---
st.markdown("""
    <style>
    /* 1. REMONTER LE CONTENU (Supprimer les marges vides en haut) */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 2. STYLE DES JOUEURS */
    /* Case pour l'utilisateur actuel (BLEU) */
    .my-card {
        background-color: #007bff;
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    /* Case pour les autres joueurs (GRIS) */
    .other-card {
        background-color: #f0f2f6;
        color: #31333F;
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-size: 14px;
        margin: 5px 0;
        border: 1px solid #e0e0e0;
    }

    /* 3. LE BUZZER (Ciblage du bouton Primary) */
    /* On transforme tout bouton "Primaire" en gros buzzer rouge rond */
    div.stButton > button[kind="primary"] {
        width: 100% !important;
        height: 220px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 30% 30%, #ff5e5e, #d60000); /* Effet 3D Rouge */
        border: 5px solid #8b0000;
        box-shadow: 
            0 15px 0 #8b0000, /* Coté 3D */
            0 15px 20px rgba(0,0,0,0.4); /* Ombre sol */
        color: white;
        font-size: 40px !important;
        font-weight: 900 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-top: 20px;
        margin-bottom: 20px;
        transition: all 0.1s;
        white-space: normal !important; /* Permet au texte de bouger */
    }

    /* Effet d'enfoncement au clic */
    div.stButton > button[kind="primary"]:active {
        transform: translateY(15px);
        box-shadow: 0 0 0 #8b0000, 0 0 10px rgba(0,0,0,0.4);
        background: radial-gradient(circle at 30% 30%, #d60000, #a00000);
    }
    
    /* Cacher la bordure de focus rouge par défaut sur mobile */
    div.stButton > button[kind="primary"]:focus:not(:active) {
        border-color: #8b0000;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- GESTION D'ÉTAT PARTAGÉ ---
@st.cache_resource
class SharedGameState:
    def __init__(self):
        self.players = {}
        self.game_active = False
        self.buzzed_player = None
        self.final_buzzed_time = 0.0
        self.start_timestamp = None
        self.accumulated_time = 0.0

    def add_player(self, name):
        if name and name not in self.players:
            self.players[name] = {'connected': False}

    def connect_player(self, name):
        if name in self.players:
            self.players[name]['connected'] = True

    def start_fresh_round(self):
        self.game_active = True
        self.buzzed_player = None
        self.accumulated_time = 0.0
        self.start_timestamp = time.time()

    def resume_round(self):
        self.game_active = True
        self.start_timestamp = time.time()
        self.buzzed_player = None

    def buzz(self, player_name):
        if self.game_active and self.buzzed_player is None:
            now = time.time()
            segment_duration = now - self.start_timestamp
            self.accumulated_time += segment_duration
            self.final_buzzed_time = self.accumulated_time
            self.buzzed_player = player_name
            self.game_active = False
            return True
        return False

    def reset_game_totally(self):
        self.game_active = False
        self.buzzed_player = None
        self.accumulated_time = 0.0
        self.start_timestamp = None

game_state = SharedGameState()

# --- UTILS ---
def play_buzzer_sound():
    sound_url = "https://www.myinstants.com/media/sounds/wrong-answer-sound-effect.mp3"
    st.markdown(f"""<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>""", unsafe_allow_html=True)

def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

# --- BARRE LATÉRALE ---
with st.sidebar:
    with st.expander("📱 QR Code Partage", expanded=False):
        img = generate_qr(APP_URL)
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf, caption="Rejoindre l'équipe", use_container_width=True)
        st.code(APP_URL, language=None)

    st.divider()

    with st.expander("⚙️ Admin Zone", expanded=False):
        password = st.text_input("Mot de passe", type="password")
        if password == "admin":
            st.success("Admin connecté")
            
            st.markdown("#### Gestion Équipe")
            c1, c2 = st.columns([2, 1])
            new_name = c1.text_input("Nom", label_visibility="collapsed", placeholder="Nom...")
            if c2.button("Ajouter"):
                game_state.add_player(new_name)
                st.rerun()

            if st.button("⚠️ Reset Total Équipe"):
                game_state.players = {}
                game_state.reset_game_totally()
                st.rerun()

            st.markdown("#### Maître du Jeu")
            # NOTE : On utilise type="secondary" ici pour ne pas qu'ils ressemblent au buzzer
            if st.button("▶️ Lancer Question", use_container_width=True):
                game_state.start_fresh_round()
                st.rerun()

            if game_state.buzzed_player:
                 if st.button("❌ Faux -> Reprendre", use_container_width=True):
                     game_state.resume_round()
                     st.rerun()
            
            if st.button("⏹️ Stop / Reset", use_container_width=True):
                game_state.reset_game_totally()
                st.rerun()

# --- LOGIQUE DE CONNEXION ---
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.current_user:
    st.title("🚨 Team Buzzer")
    if not game_state.players:
        st.info("Attente de l'admin pour créer l'équipe...")
    else:
        options = ["-- Qui êtes-vous ? --"] + [p for p in game_state.players.keys() if not game_state.players[p]['connected']]
        choice = st.selectbox("", options)
        if st.button("Valider", type="primary") and choice != "-- Qui êtes-vous ? --":
            st.session_state.current_user = choice
            game_state.connect_player(choice)
            st.rerun()

# --- ÉCRAN DE JEU ---
else:
    me = st.session_state.current_user
    
    # --- 1. AFFICHAGE DE L'ÉQUIPE (GRILLE) ---
    # On affiche d'abord la liste pour que ce soit en haut
    st.caption("L'Équipe en direct :")
    
    # On crée des colonnes dynamiques (4 par ligne)
    player_names = list(game_state.players.keys())
    
    # Boucle pour afficher les joueurs par ligne de 4
    for i in range(0, len(player_names), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(player_names):
                p_name = player_names[i + j]
                p_data = game_state.players[p_name]
                icon = "✅" if p_data['connected'] else "⏳"
                
                with cols[j]:
                    # SI C'EST MOI -> Style Bleu (.my-card)
                    if p_name == me:
                        st.markdown(f"<div class='my-card'>{icon} {p_name} (Moi)</div>", unsafe_allow_html=True)
                    # SI C'EST UN AUTRE -> Style Gris (.other-card)
                    else:
                        st.markdown(f"<div class='other-card'>{icon} {p_name}</div>", unsafe_allow_html=True)

    st.divider()

    # --- 2. ZONE DE JEU (Fragment = Refresh rapide) ---
    @st.fragment(run_every=0.2)
    def game_zone():
        
        # CAS 1 : JEU ACTIF (ON ATTEND LE BUZZ)
        if game_state.game_active:
            st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>À VOS MARQUES...</h2>", unsafe_allow_html=True)
            
            # Pour centrer le buzzer, on utilise 3 colonnes, buzzer au milieu
            c_left, c_buzzer, c_right = st.columns([1, 2, 1])
            with c_buzzer:
                # BOUTON TYPE PRIMARY = Le style CSS Rouge s'applique ici
                if st.button("BUZZ !", type="primary"):
                    game_state.buzz(me)
                    st.rerun()

            # Affichage du chrono
            if game_state.start_timestamp:
                t = (time.time() - game_state.start_timestamp) + game_state.accumulated_time
                st.markdown(f"<p style='text-align: center; font-size: 20px; color: #666;'>⏱️ {t:.2f} s</p>", unsafe_allow_html=True)

        # CAS 2 : QUELQU'UN A BUZZÉ
        elif game_state.buzzed_player:
            st.markdown("<h1 style='text-align: center; font-size: 60px; margin-top: 0;'>🚨 STOP !</h1>", unsafe_allow_html=True)
            
            winner = game_state.buzzed_player
            color = "#007bff" if winner == me else "#dc3545" # Bleu si c'est moi, Rouge si c'est l'autre
            
            st.markdown(
                f"""
                <div style='background-color: {color}; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;'>
                    <h2 style='margin:0;'>{winner}</h2>
                    <h1 style='margin:0; font-size: 50px;'>{game_state.final_buzzed_time:.2f}s</h1>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            play_buzzer_sound()
            
            if winner == me:
                st.success("🎤 C'est à vous de répondre !")
            else:
                st.info(f"🤫 Silence, {winner} réfléchit...")

        # CAS 3 : PAUSE / ATTENTE
        else:
            st.markdown(
                """
                <div style='text-align: center; color: grey; margin-top: 40px;'>
                    <h3>⏸️ En attente de l'animateur</h3>
                    <p>Préparez-vous...</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

    game_zone()
