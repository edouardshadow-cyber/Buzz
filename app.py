import streamlit as st
import time
import qrcode
from io import BytesIO

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Team Buzzer", page_icon="🚨", layout="centered")

# --- URL DE VOTRE APP ---
APP_URL = "https://jmgdqtj4u9obietzmgj2hg.streamlit.app/"

# --- URL DE L'IMAGE REALISTE DU BUZZER ---
# J'utilise un lien public fiable vers un bouton très similaire à votre demande.
# Si le lien casse un jour, il faudra le remplacer par le vôtre ou une image en base64.
REALISTIC_BUZZER_URL = "https://i.imgur.com/J3M8iqP.png"

# --- CSS ET STYLE (MODIFIÉ POUR L'IMAGE RÉALISTE) ---
st.markdown(f"""
    <style>
    /* 1. REMONTER LE CONTENU */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }}
    
    /* 2. STYLE DES JOUEURS */
    .my-card {{
        background-color: #007bff;
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    .other-card {{
        background-color: #f0f2f6;
        color: #31333F;
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-size: 14px;
        margin: 5px 0;
        border: 1px solid #e0e0e0;
    }}

    /* 3. LE BUZZER IMAGE RÉALISTE */
    /* On cible le bouton "Primary" */
    div.stButton > button[kind="primary"] {{
        /* Taille de l'image */
        width: 280px !important;
        height: 280px !important;
        
        /* On retire les styles de bouton par défaut */
        border: none !important;
        border-radius: 0 !important;
        background-color: transparent !important;
        box-shadow: none !important;
        
        /* On applique l'image comme fond */
        background-image: url('{REALISTIC_BUZZER_URL}') !important;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        
        /* Centrage */
        margin: 20px auto;
        display: block;
        
        transition: transform 0.1s;
    }}

    /* IMPORTANT : On cache le texte "BUZZ !" qui est DANS le bouton pour ne voir que l'image */
    div.stButton > button[kind="primary"] p {{
        display: none !important;
    }}

    /* Effet d'enfoncement simple au clic */
    div.stButton > button[kind="primary"]:active {{
        transform: scale(0.97) translateY(5px);
    }}
    
    /* Cacher la bordure de focus sur mobile */
    div.stButton > button[kind="primary"]:focus:not(:active) {{
        border: none !important;
        color: transparent !important;
    }}
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
            # NOTE : type="secondary" pour ne pas qu'ils ressemblent au buzzer
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
    
    # --- 1. AFFICHAGE DE L'ÉQUIPE ---
    st.caption("L'Équipe en direct :")
    player_names = list(game_state.players.keys())
    for i in range(0, len(player_names), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(player_names):
                p_name = player_names[i + j]
                p_data = game_state.players[p_name]
                icon = "✅" if p_data['connected'] else "⏳"
                with cols[j]:
                    if p_name == me:
                        st.markdown(f"<div class='my-card'>{icon} {p_name} (Moi)</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='other-card'>{icon} {p_name}</div>", unsafe_allow_html=True)

    st.divider()

    # --- 2. ZONE DE JEU (Fragment = Refresh rapide) ---
    @st.fragment(run_every=0.2)
    def game_zone():
        
        # CAS 1 : JEU ACTIF (ON ATTEND LE BUZZ)
        if game_state.game_active:
            st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>À VOS MARQUES...</h2>", unsafe_allow_html=True)
            
            # Centrage du buzzer
            c_left, c_buzzer, c_right = st.columns([1, 3, 1])
            with c_buzzer:
                # BOUTON TYPE PRIMARY = L'image du buzzer s'applique ici
                # Le texte "BUZZ !" est caché par le CSS
                if st.button("BUZZ !", type="primary"):
                    game_state.buzz(me)
                    st.rerun()

            # Affichage du chrono
            if game_state.start_timestamp:
                t = (time.time() - game_state.start_timestamp) + game_state.accumulated_time
                st.markdown(f"<p style='text-align: center; font-size: 20px; color: #666; margin-top: 10px;'>⏱️ {t:.2f} s</p>", unsafe_allow_html=True)

        # CAS 2 : QUELQU'UN A BUZZÉ
        elif game_state.buzzed_player:
            st.markdown("<h1 style='text-align: center; font-size: 60px; margin-top: 0;'>🚨 STOP !</h1>", unsafe_allow_html=True)
            
            winner = game_state.buzzed_player
            color = "#007bff" if winner == me else "#dc3545"
            
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
