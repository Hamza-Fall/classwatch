import streamlit as st
import anthropic
import base64
import json
from datetime import datetime
from PIL import Image
import io
import requests  # Nécessaire pour récupérer la météo en temps réel

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ClassWatch · Gestion des incidents",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS — Design épuré et moderne
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #F4F6FA;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: none;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #F8FAFC !important;
}

/* ── Header ── */
.cw-header {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 20px;
    box-shadow: 0 4px 24px rgba(15,23,42,0.18);
}
.cw-header-icon {
    font-size: 48px;
    line-height: 1;
}
.cw-header-title {
    color: #F8FAFC;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0;
}
.cw-header-sub {
    color: #94A3B8;
    font-size: 14px;
    margin: 4px 0 0 0;
}

/* ── Cards ── */
.cw-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(15,23,42,0.07);
    margin-bottom: 20px;
    border: 1px solid #E2E8F0;
}
.cw-card-title {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748B;
    margin-bottom: 16px;
}

/* ── Incident badges ── */
.incident-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    margin: 4px 4px 4px 0;
}
.badge-danger  { background:#FEE2E2; color:#DC2626; }
.badge-warning { background:#FEF9C3; color:#CA8A04; }
.badge-success { background:#DCFCE7; color:#16A34A; }
.badge-info    { background:#DBEAFE; color:#2563EB; }

/* ── Status indicator ── */
.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
}
.dot-green  { background: #22C55E; box-shadow: 0 0 6px #22C55E88; }
.dot-red    { background: #EF4444; box-shadow: 0 0 6px #EF444488; }
.dot-yellow { background: #EAB308; box-shadow: 0 0 6px #EAB30888; }

/* ── History items ── */
.history-item {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    position: relative;
}
.history-time {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #94A3B8;
}
.history-severity-high   { border-left: 4px solid #EF4444; }
.history-severity-medium { border-left: 4px solid #EAB308; }
.history-severity-low    { border-left: 4px solid #22C55E; }

/* ── Stat cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 20px;
}
.stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 6px rgba(15,23,42,0.05);
}
.stat-number {
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
}
.stat-label {
    font-size: 12px;
    color: #64748B;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Streamlit overrides ── */
.stButton > button {
    background: #1E293B;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 15px;
    width: 100%;
    transition: all 0.2s;
    box-shadow: 0 2px 8px rgba(15,23,42,0.2);
}
.stButton > button:hover {
    background: #334155;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(15,23,42,0.3);
}
div[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #CBD5E1;
    border-radius: 12px;
    padding: 12px;
}
.stSpinner > div {
    border-color: #1E293B transparent transparent transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FONCTION METEO (Open-Meteo API)
# ─────────────────────────────────────────────
@st.cache_data(ttl=900)  # Conserve la météo en cache pendant 15 minutes
def get_weather_data():
    try:
        # Coordonnées par défaut (Exemple : Paris. Latitude: 48.8566, Longitude: 2.3522)
        url = "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current_weather=true"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            temp = data["current_weather"]["temperature"]
            code = data["current_weather"]["weathercode"]
            return temp, code
    except Exception:
        pass
    return None, None

# Récupération des données météo extérieures
ext_temp, weather_code = get_weather_data()

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏫 ClassWatch")
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")

    # Chargement de la clé API
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input(
            "Clé API Anthropic",
            type="password",
            placeholder="sk-ant-...",
            help="Obtiens ta clé sur console.anthropic.com"
        )
    else:
        st.success("🔑 Clé API chargée automatiquement")

    st.markdown("---")
    st.markdown("### 🎯 Incidents détectés")

    checks = {
        "👨‍🏫 Présence du professeur": True,
        "🪑 Chaises renversées": True,
        "💻 Ordinateurs allumés": True,
        "🎒 Affaires abandonnées": True,
        "🚪 Portes ouvertes": True,
        "📺 Écran allumé": True,
        "🏃 Élèves debout": True,
        "🔇 Ambiance calme": True,
    }

    selected_checks = {}
    for label, default in checks.items():
        selected_checks[label] = st.checkbox(label, value=default)

    st.markdown("---")
    st.markdown("### 📊 Session")
    st.markdown(f"**Analyses effectuées :** {len(st.session_state.history)}")

    if st.button("🗑️ Effacer l'historique"):
        st.session_state.history = []
        st.session_state.last_analysis = None
        st.rerun()

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="cw-header">
    <div class="cw-header-icon">🏫</div>
    <div>
        <div class="cw-header-title">ClassWatch — Gestion des incidents</div>
        <div class="cw-header-sub">Analysez votre salle de classe en temps réel grâce à l'IA</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  STATS ROW
# ─────────────────────────────────────────────
total   = len(st.session_state.history)
high    = sum(1 for h in st.session_state.history if h.get("severity") == "high")
medium  = sum(1 for h in st.session_state.history if h.get("severity") == "medium")

st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-number" style="color:#1E293B">{total}</div>
        <div class="stat-label">Analyses totales</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" style="color:#EF4444">{high}</div>
        <div class="stat-label">Incidents critiques</div>
    </div>
    <div class="stat-card">
        <div class="stat-number" style="color:#EAB308">{medium}</div>
        <div class="stat-label">Alertes modérées</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MAIN LAYOUT
# ─────────────────────────────────────────────
col_left, col_right = st.columns([1.1, 1], gap="large")

# ── LEFT: Upload + Analyse ──
with col_left:
    st.markdown('<div class="cw-card">', unsafe_allow_html=True)
    st.markdown('<div class="cw-card-title">📷 Photo de la salle</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Glisse une photo ici ou clique pour en choisir une",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, use_container_width=True, caption="Aperçu de la photo")

    st.markdown("</div>", unsafe_allow_html=True)

    analyze_btn = st.button("🔍 Analyser la salle", disabled=(not uploaded or not api_key))

    if not api_key:
        st.info("💡 Entre ta clé API Anthropic dans la barre latérale pour commencer.")
    elif not uploaded:
        st.info("💡 Charge une photo de ta salle pour lancer l'analyse.")

# ── RIGHT: Résultats ──
with col_right:
    
    # ── BLOC MÉTÉO & CLIMATISATION ──
    st.markdown('<div class="cw-card">', unsafe_allow_html=True)
    st.markdown('<div class="cw-card-title">🌤| Conditions Thermiques & Météo</div>', unsafe_allow_html=True)
    if ext_temp is not None:
        need_clim = ext_temp >= 26.0
        clim_badge = '<span class="incident-badge badge-danger">❄️ AC Requise (Chaud)</span>' if need_clim else '<span class="incident-badge badge-success">🍃 Température OK (Pas de clim)</span>'
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <span style="font-size: 24px; font-weight: 700; color:#1E293B;">{ext_temp}°C</span>
                <p style="margin:0; color:#64748B; font-size:13px;">Température extérieure actuelle</p>
            </div>
            <div>{clim_badge}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#64748B; font-size:13px;'>Impossible de charger la météo en temps réel.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.last_analysis:
        data = st.session_state.last_analysis

        sev = data.get("severity", "low")
        sev_config = {
            "high":   ("dot-red",    "badge-danger",  "⚠️ Critique",  "Intervention requise"),
            "medium": ("dot-yellow", "badge-warning", "⚡ Modéré",    "Surveiller"),
            "low":    ("dot-green",  "badge-success", "✅ Normal",    "Tout va bien"),
        }
        dot_cls, badge_cls, sev_label, sev_sub = sev_config.get(sev, sev_config["low"])

        st.markdown(f"""
        <div class="cw-card">
            <div class="cw-card-title">📊 Statut général</div>
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                <span class="status-dot {dot_cls}"></span>
                <span class="incident-badge {badge_cls}">{sev_label}</span>
                <span style="color:#64748B;font-size:14px">{sev_sub}</span>
            </div>
            <p style="color:#1E293B;font-size:15px;line-height:1.6;margin:0">{data.get('summary','')}</p>
        </div>
        """, unsafe_allow_html=True)

        incidents = data.get("incidents", [])
        if incidents:
            badges_html = ""
            for inc in incidents:
                lvl = inc.get("level", "info")
                cls_map = {"danger": "badge-danger", "warning": "badge-warning",
                           "success": "badge-success", "info": "badge-info"}
                icon_map = {"danger": "🚨", "warning": "⚠️", "success": "✅", "info": "ℹ️"}
                cls  = cls_map.get(lvl, "badge-info")
                icon = icon_map.get(lvl, "ℹ️")
                badges_html += f'<span class="incident-badge {cls}">{icon} {inc.get("label","")}</span>'

            st.markdown(f"""
            <div class="cw-card">
                <div class="cw-card-title">🎯 Incidents & observations</div>
                {badges_html}
            </div>
            """, unsafe_allow_html=True)

        recs = data.get("recommendations", [])
        if recs:
            recs_html = "".join(
                f'<div style="display:flex;gap:10px;margin-bottom:10px">'
                f'<span style="color:#6366F1;font-weight:700;font-size:18px">→</span>'
                f'<span style="color:#1E293B;font-size:14px;line-height:1.5">{r}</span>'
                f'</div>'
                for r in recs
            )
            st.markdown(f"""
            <div class="cw-card">
                <div class="cw-card-title">💡 Recommandations</div>
                {recs_html}
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="cw-card" style="text-align:center;padding:48px 24px">
            <div style="font-size:56px;margin-bottom:16px">🔍</div>
            <div style="font-size:18px;font-weight:600;color:#1E293B;margin-bottom:8px">
                Aucune analyse en cours
            </div>
            <div style="color:#94A3B8;font-size:14px">
                Charge une photo et clique sur "Analyser la salle"
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANALYSE LOGIC
# ─────────────────────────────────────────────
def encode_image(file) -> tuple[str, str]:
    """Encode l'image en base64 de manière sécurisée en UTF-8."""
    ext = file.name.split(".")[-1].lower()
    media_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "png": "image/png", "webp": "image/webp"}
    media_type = media_map.get(ext, "image/jpeg")
    
    raw_bytes = file.getvalue()
    data = base64.b64encode(raw_bytes).decode("utf-8")
    return data, media_type


def build_prompt(active_checks: list[str], temperature: float) -> str:
    checks_str = "\n".join(f"- {c}" for c in active_checks)
    
    clim_instruction = ""
    if temperature is not None:
        clim_instruction = f"- ATTENTION CONTEXTE THERMIQUE : La température extérieure est actuellement de {temperature}°C. Si elle est élevée (ex: >= 26°C), vérifie visuellement sur l'image si la climatisation semble nécessaire, si des fenêtres sont restées ouvertes anormalement, et ajoute une recommandation adaptée."

    return f"""Tu es un système expert de surveillance de salle de classe.
Analyse cette photo et retourne UNIQUEMENT un objet JSON valide (sans balises markdown, sans texte avant/après).

Points à vérifier :
{checks_str}
{clim_instruction}

Structure JSON attendue :
{{
  "severity": "high" | "medium" | "low",
  "summary": "Résumé en 1-2 phrases de l'état général de la salle",
  "incidents": [
    {{
      "label": "Nom court de l'incident",
      "level": "danger" | "warning" | "success" | "info",
      "detail": "Description précise"
    }}
  ],
  "recommendations": [
    "Action concrète recommandée 1",
    "Action concrète recommandée 2"
  ]
}}

Règles :
- severity=high si un incident critique (chaise renversée, prof absent, danger visible)
- severity=medium si situation anormale mais pas urgente
- severity=low si tout est normal
- Sois précis et factuel, base-toi uniquement sur ce que tu vois
- Réponds EXCLUSIVEMENT en JSON valide"""


if analyze_btn and uploaded and api_key:
    # Encodage en base64 nettoyé (UTF-8)
    img_data, media_type = encode_image(uploaded)

    # Récupération sécurisée des options cochées
    active = [label for label, checked in selected_checks.items() if checked]
    
    # Génération et nettoyage forcé du prompt au format UTF-8 pur
    prompt_brut = build_prompt(active, ext_temp)
    prompt_utf8 = prompt_brut.encode('utf-8', errors='ignore').decode('utf-8')

    with st.spinner("🤖 Analyse en cours…"):
        try:
            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": img_data,
                                },
                            },
                            {"type": "text", "text": prompt_utf8},
                        ],
                    }
                ],
            )

            # Nettoyage et encadrement strict de la chaîne de sortie
            raw = message.content[0].text.strip()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            else:
                raw = str(raw).encode("utf-8", errors="ignore").decode("utf-8")
                
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(raw, strict=False)
            result["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Nettoyage UTF-8 du nom de fichier pour l'historique
            safe_filename = uploaded.name.encode('utf-8', errors='ignore').decode('utf-8')
            result["filename"]  = safe_filename

            st.session_state.last_analysis = result
            st.session_state.history.insert(0, result)
            st.rerun()

        except json.JSONDecodeError:
            st.error("❌ L'IA n'a pas retourné un JSON valide. Réessaie.")
        except anthropic.AuthenticationError:
            st.error("❌ Clé API invalide. Vérifie ta clé dans la barre latérale.")
        except Exception as e:
            st.error(f"❌ Erreur inattendue : {e}")

# ─────────────────────────────────────────────
#  HISTORIQUE
# ─────────────────────────────────────────────
if st.session_state.history:
    st.markdown("---")
    st.markdown('<div class="cw-card-title" style="margin-bottom:16px">🕐 Historique des analyses</div>',
                unsafe_allow_html=True)

    for item in st.session_state.history:
        sev = item.get("severity", "low")
        sev_cls = {"high": "history-severity-high",
                   "medium": "history-severity-medium",
                   "low": "history-severity-low"}.get(sev, "history-severity-low")
        emoji  = {"high": "🚨", "medium": "⚡", "low": "✅"}.get(sev, "✅")
        n_inc  = len(item.get("incidents", []))

        st.markdown(f"""
        <div class="history-item {sev_cls}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <span style="font-weight:600;font-size:14px;color:#1E293B">
                    {emoji} {item.get('filename','photo')}
                </span>
                <span class="history-time">{item.get('timestamp','')}</span>
            </div>
            <div style="color:#475569;font-size:13px">{item.get('summary','')}</div>
            <div style="margin-top:6px;color:#94A3B8;font-size:12px">{n_inc} incident(s) détecté(s)</div>
        </div>
        """, unsafe_allow_html=True)
