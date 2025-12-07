import streamlit as st
import time
import qrcode
from PIL import Image
from io import BytesIO

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Team Buzzer", page_icon="🚨", layout="centered")

# --- URL DE VOTRE APP (Pour le QR Code) ---
APP_URL = "https://jmgdqtj4u9obietzmgj2hg.streamlit.app/"

# --- CSS PERSONNALISÉ (STYLE DU BUZZER 3D) ---
st.markdown("""
    <style>
    /* Style global pour centrer les éléments */
    .block-container {
        padding-top: 2rem;
    }

    /* LE STYLE DU BUZZER ARCADE 3D */
    /* On cible le bouton spécifique qui contient le texte "BUZZ" vide */
    div.stButton > button.buzzer-style {
        width: 200px !important;
        height: 200px !important;
        border-radius: 50% !important;
        background: radial-gradient(circle at 30% 30%, #ff4d4d, #cc0000);
        border: 4px solid #8b0000;
        box-shadow: 
            0 10px 0 #8b0000, /* L'épaisseur 3D du bouton */
            0 10px 20px rgba(0,0,0,0.4), /* L'ombre portée au sol */
            inset 0 10px 20px rgba(255,255,255,0.4); /* Le reflet brillant dessus */
        color: white;
        font-weight: bold;
        font-size: 24px;
        transition: all 0.1s;
        margin: 0 auto;
        display: block;
    }

    /* Effet quand on appuie dessus */
    div.stButton > button.buzzer-style:active {
        transform: translateY(10px); /* Le bouton descend */
        box-shadow: 
            0 0 0 #8b0000, /* L'épaisseur 3D disparait */
            0 0 5px rgba(0,0,0,0.4), /* L'ombre se réduit */
            inset 0 10px 20px rgba(255,255,255,0.4);
    }
    
    /* Retirer le focus rouge vilain sur mobile */
    div.stButton > button.buzzer-style:focus:not(:active) {
        border-color: #8b0000;
        color: white;
    }

    /* Style des joueurs */
    .player-status {
        font-size: 16px;
        margin: 2px;
        padding: 5px;
        border-radius: 5px;
        background-color: #f1f3f6;
        text-align: center;
        border: 1px solid #ddd;
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

# --- FONCTION AUDIO ---
def play_buzzer_sound():
    sound_url = "https://www.myinstants.com/media/sounds/wrong-answer-sound-effect.mp3"
    st.markdown(f"""<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>""", unsafe_allow_html=True)

# --- FONCTION QR CODE ---
def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# --- BARRE LATÉRALE ---
with st.sidebar:
    
    # --- SECTION PARTAGE ---
    with st.expander("📱 Partager l'app", expanded=False):
        img = generate_qr(APP_URL)
        buf = BytesIO()
        img.save(buf)
        st.image(buf, caption="Scannez pour rejoindre", use_container_width=True)
        st.code(APP_URL, language=None)

    st.divider()

    # --- SECTION ADMIN (DANS UN EXPANDER, PLUS STABLE QUE POPOVER) ---
    with st.expander("⚙️ Admin", expanded=False):
        password = st.text_input("Mot de passe", type="password")
        if password == "admin":
            st.success("Connecté")
            
            st.markdown("#### 1. Équipe")
            col_add1, col_add2 = st.columns([2, 1])
            new_member = col_add1.text_input("Nom", label_visibility="collapsed", placeholder="Nom...")
            if col_add2.button("Ajouter"):
                game_state.add_player(new_member)
                st.rerun()

            if st.button("⚠️ Vider l'équipe"):
                game_state.players = {}
                game_state.reset_game_totally()
                st.rerun()

            st.markdown("#### 2. Jeu")
            
            # Boutons de contrôle classiques
            if st.button("▶️ GO ! (Start)", type="primary", use_container_width=True):
                game_state.start_fresh_round()
                st.rerun()

            if game_state.buzzed_player:
                 if st.button("❌ Faux -> Relancer", use_container_width=True):
                     game_state.resume_round()
                     st.rerun()
            
            if st.button("⏹️ Reset Manche", use_container_width=True):
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
        st.info("Attente de l'admin...")
    else:
        options = ["-- Moi c'est... --"] + [p for p in game_state.players.keys() if not game_state.players[p]['connected']]
        choice = st.selectbox("", options)
        
        if st.button("Valider") and choice != "-- Moi c'est... --":
            st.session_state.current_user = choice
            game_state.connect_player(choice)
            st.rerun()

# --- INTERFACE JEU ---
else:
    current_user = st.session_state.current_user
    
    # Header compact
    cols_header = st.columns([1, 3])
    cols_header[0].markdown(f"**{current_user}**")
    with cols_header[1]:
        cols_players = st.columns(5)
        for idx, (name, data) in enumerate(game_state.players.items()):
            icon = "🟢" if data['connected'] else "⚪"
            # On affiche juste l'icone pour gagner de la place si beaucoup de joueurs
            with cols_players[idx % 5]:
                 st.markdown(f"<div title='{name}'>{icon}</div>", unsafe_allow_html=True)
    
    st.divider()

    # Zone de jeu avec rafraichissement rapide
    @st.fragment(run_every=0.2)
    def game_zone():
        # Astuce CSS pour appliquer le style "buzzer-style" au bouton Python ci-dessous
        # Streamlit ne permet pas de mettre des classes directement, donc on triche avec le JavaScript/CSS
        # Le bouton ci-dessous aura un ID interne, on applique le style global défini en haut
        
        if game_state.game_active:
            st.markdown("<h2 style='text-align: center;'>PRÊTS ?</h2>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                # Le bouton a des espaces pour le rendre large, mais le CSS va forcer la forme ronde
                # On utilise type="primary" pour aider le ciblage si besoin, mais le CSS fait le gros du travail
                if st.button("BUZZ !", key="the_buzzer"): 
                    game_state.buzz(current_user)
                    st.rerun()

            # Application forcée du style CSS sur ce bouton spécifique via JavaScript hack léger
            # C'est nécessaire car Streamlit isole les composants
            st.markdown("""
                <script>
                const buttons = window.parent.document.querySelectorAll('button');
                buttons.forEach(btn => {
                    if (btn.innerText.includes("BUZZ !")) {
                        btn.classList.add("buzzer-style");
                    }
                });
                </script>
                """, unsafe_allow_html=True)
            
            if game_state.start_timestamp:
                current_segment_time = time.time() - game_state.start_timestamp
                total_time_live = game_state.accumulated_time + current_segment_time
                st.markdown(f"<h3 style='text-align: center; color: grey;'>⏱️ {total_time_live:.2f} s</h3>", unsafe_allow_html=True)

        elif game_state.buzzed_player:
            st.markdown("<h1 style='text-align: center; font-size: 60px;'>🚨 BUZZ !</h1>", unsafe_allow_html=True)
            winner_color = "#28a745" if current_user == game_state.buzzed_player else "#dc3545"
            st.markdown(f"<h2 style='text-align: center; color: {winner_color};'>{game_state.buzzed_player}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>{game_state.final_buzzed_time:.2f} s</h3>", unsafe_allow_html=True)
            play_buzzer_sound()
            
            if current_user == game_state.buzzed_player:
                 st.success("À vous de répondre !")
            else:
                 st.info("Silence...")

        else:
            st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: grey;'>⏸️ Pause</h3>", unsafe_allow_html=True)

    game_zone()
