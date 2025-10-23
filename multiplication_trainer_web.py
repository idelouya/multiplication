import time
import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Try to enable 1s auto-refresh for the live countdown (optional)
HAVE_AUTOREFRESH = False
try:
    from streamlit_extras.st_autorefresh import st_autorefresh  # pip install streamlit-extras
    HAVE_AUTOREFRESH = True
except Exception:
    HAVE_AUTOREFRESH = False

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Multiplication Trainer", page_icon="🧮", layout="centered")

# ---------------------- GLOBAL STYLES (Cream → Peach + Mobile) ----------------------
st.markdown("""
<style>
/* Background gradient */
[data-testid="stAppViewContainer"]{
  background: linear-gradient(180deg, #FFF8F0 0%, #FFE6D5 100%);
}
/* General font */
body, div, label { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color:#2d2d2d; }
/* Cards */
.card{
  background:#fff; border-radius:16px; padding:20px;
  box-shadow:0 6px 18px rgba(0,0,0,0.06); margin-bottom:18px;
}
/* Mint buttons */
div.stButton > button:first-child{
  background:#22C55E; color:#fff; border:none; border-radius:10px;
  font-weight:700; height:3em;
}
div.stButton > button:first-child:hover{ background:#16A34A; color:#fff; }
/* Toggle buttons row */
.toggle-row button{
  height:3em; border-radius:10px; font-weight:700;
}
/* Quiz label + center input */
.quiz-label{ text-align:center; font-size:1.1rem; font-weight:700; color:#14532D; margin-top:8px; }
/* Smaller screens */
@media (max-width: 600px){
  .block-container{ padding: 0.6rem 0.6rem !important; }
  h1{ font-size:1.4rem !important; text-align:center; }
  h2{ font-size:1.25rem !important; }
  h3{ font-size:1.1rem !important; }
  div.stButton > button:first-child{ width:100% !important; }
  .toggle-row button{ width:100% !important; margin-bottom:8px; }
  label, p, span{ font-size: 0.96rem !important; }
}
/* Footer */
.footer{ text-align:center; color:#777; font-size:12px; margin-top:36px; margin-bottom:6px; }
</style>
""", unsafe_allow_html=True)

# ---------------------- i18n ----------------------
STR = {
    "fr": {
        "title": "Multiplication Trainer",
        "lang_fr": "Français", "lang_en": "English",
        "kids_zone": "Espace Enfant", "parents_zone": "Espace Parent",
        "tables_label": "Tables de multiplication (0 à 12)",
        "keyboard_mode": "✏️ Entrer la réponse au clavier",
        "timer_enable": "⏳ Activer le chrono par question",
        "duration_seconds": "Durée (secondes)",
        "start_quiz": "▶ Démarrer le quiz",
        "retry_mistakes": "🔁 Rejouer mes erreurs",
        "question": "Question", "correct": "Correct",
        "enter_answer": "Tape ta réponse au clavier :", "submit": "Valider",
        "too_slow": "⏳ Trop lent !", "oops": "❌ Oups", "bravo": "✅ Bravo !",
        "finished": "Terminé !",
        "badge_mastered": "🏅 Maîtrisé !",
        "badge_almost": "⭐ Presque parfait !",
        "badge_keep": "💪 Continue d'essayer !",
        "results_fmt": "Résultats : {correct}/{total} ({percent}%).",
        "no_tables": "Choisis au moins une table.", "no_mistakes": "Aucune erreur enregistrée pour le moment.",
        "review_mistakes": "📄 Voir erreurs", "progress_chart": "📊 Graphique de progrès",
        "export_csv": "💾 Télécharger erreurs (CSV)", "reset_all": "♻ Réinitialiser tout",
        "per_table_summary": "Progrès par table (correct / essais)",
        "footer": "© 2025 Multiplication Trainer – Développé par Illan Delouya",
        "fun_title": "🎯 Multiplions en s'amusant !",
        "toggle_kids": "🧒 Enfant", "toggle_parent": "👨‍👩‍👧 Parent",
        "progress": "Progrès",
        "timer_note": "Astuce : si le décompte ne bouge pas, l'auto-rafraîchissement n'est pas actif (ajoute 'streamlit-extras' dans requirements)."
    },
    "en": {
        "title": "Multiplication Trainer",
        "lang_fr": "French", "lang_en": "English",
        "kids_zone": "Kids Zone", "parents_zone": "Parents’ Zone",
        "tables_label": "Times tables (0 to 12)",
        "keyboard_mode": "✏️ Type answer with keyboard",
        "timer_enable": "⏳ Enable per-question timer",
        "duration_seconds": "Duration (seconds)",
        "start_quiz": "▶ Start quiz",
        "retry_mistakes": "🔁 Retry mistakes",
        "question": "Question", "correct": "Correct",
        "enter_answer": "Type your answer:", "submit": "Submit",
        "too_slow": "⏳ Too slow!", "oops": "❌ Oops!", "bravo": "✅ Great job!",
        "finished": "Finished!",
        "badge_mastered": "🏅 Mastered!", "badge_almost": "⭐ Almost perfect!",
        "badge_keep": "💪 Keep practicing!",
        "results_fmt": "Results: {correct}/{total} ({percent}%).",
        "no_tables": "Please select at least one table.", "no_mistakes": "No mistakes recorded yet.",
        "review_mistakes": "📄 Review mistakes", "progress_chart": "📊 Progress chart",
        "export_csv": "💾 Download errors (CSV)", "reset_all": "♻ Reset all",
        "per_table_summary": "Progress by table (correct / attempts)",
        "footer": "© 2025 Multiplication Trainer – Developed by Illan Delouya",
        "fun_title": "🎯 Fun Multiplications!",
        "toggle_kids": "🧒 Kids", "toggle_parent": "👨‍👩‍👧 Parent",
        "progress": "Progress",
        "timer_note": "Tip: if seconds aren’t moving, enable auto-refresh by adding 'streamlit-extras' to requirements."
    },
}

# ---------------------- State ----------------------
def init_state():
    ss = st.session_state
    ss.setdefault("lang", "fr")
    ss.setdefault("view", "kids")  # "kids" or "parent"
    ss.setdefault("selected_tables", [0,1,2,3])
    ss.setdefault("keyboard_mode", True)
    ss.setdefault("timer_on", True)
    ss.setdefault("perq_seconds", 8)
    # quiz state
    ss.setdefault("in_quiz", False)
    ss.setdefault("questions", [])
    ss.setdefault("q_idx", 0)
    ss.setdefault("correct", 0)
    ss.setdefault("deadline", None)
    ss.setdefault("pending_next", False)
    ss.setdefault("next_time", 0.0)
    ss.setdefault("feedback", "")
    # stats & errors
    ss.setdefault("tables_stats", {})
    ss.setdefault("errors", [])
init_state()

def t(k): return STR[st.session_state.lang][k]

# ---------------------- Header & Language ----------------------
st.markdown(f"<h1 style='text-align:center;'>{t('fun_title')}</h1>", unsafe_allow_html=True)
cL, cR = st.columns(2)
with cL:
    if st.button("✅ Français" if st.session_state.lang=="fr" else "Français", use_container_width=True):
        st.session_state.lang = "fr"; st.rerun()
with cR:
    if st.button("English" if st.session_state.lang=="fr" else "✅ English", use_container_width=True):
        st.session_state.lang = "en"; st.rerun()

# ---------------------- View Toggle (two wide buttons) ----------------------
st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    if st.button(t("toggle_kids"), use_container_width=True, key="btn_kids"):
        st.session_state.view = "kids"; st.rerun()
with b2:
    if st.button(t("toggle_parent"), use_container_width=True, key="btn_parent"):
        st.session_state.view = "parent"; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------- Helpers ----------------------
def build_questions_from_tables(tables):
    qs = [{"a": a, "b": b, "answer": a*b} for a in tables for b in range(1,13)]
    random.shuffle(qs); return qs

def update_table_stats(a_table, ok):
    stats = st.session_state.tables_stats.setdefault(a_table, {"attempts":0, "correct":0})
    stats["attempts"] += 1
    if ok: stats["correct"] += 1

def add_error(a, b, correct_answer, user_answer, outcome):
    st.session_state.errors.append({
        "ts": int(time.time()), "a": int(a), "b": int(b),
        "correct_answer": int(correct_answer),
        "user_answer": (None if user_answer is None else int(user_answer)),
        "outcome": outcome, "resolved": False
    })

def start_quiz():
    if not st.session_state.selected_tables:
        st.warning(t("no_tables")); return
    st.session_state.questions = build_questions_from_tables(st.session_state.selected_tables)
    st.session_state.q_idx = 0; st.session_state.correct = 0
    st.session_state.feedback = ""; st.session_state.pending_next = False
    st.session_state.in_quiz = True
    st.session_state.deadline = (time.time() + st.session_state.perq_seconds) if st.session_state.timer_on else None
    st.rerun()

def end_quiz():
    ss = st.session_state
    total = len(ss.questions); correct = ss.correct
    pct = round(100*correct/max(1,total))
    if pct==100: badge = t("badge_mastered")
    elif pct>=85: badge = t("badge_almost")
    else: badge = t("badge_keep")
    st.success(f"**{t('finished')}** 🎉\n\n{badge}\n\n" + t("results_fmt").format(correct=correct,total=total,percent=pct))
    ss.in_quiz=False; ss.questions=[]; ss.q_idx=0; ss.correct=0
    ss.deadline=None; ss.feedback=""; ss.pending_next=False

# ---------------------- KIDS VIEW ----------------------
if st.session_state.view == "kids":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(t("kids_zone"))

    st.caption(t("tables_label"))
    # 3 columns for better mobile usability
    cols = st.columns(3)
    selected = []
    for i in range(13):
        c = cols[i % 3]
        with c:
            if st.checkbox(str(i), value=(i in st.session_state.selected_tables), key=f"table_{i}"):
                selected.append(i)
    st.session_state.selected_tables = selected

    oc1, oc2, oc3 = st.columns(3)
    with oc1: st.session_state.keyboard_mode = st.checkbox(t("keyboard_mode"), value=st.session_state.keyboard_mode)
    with oc2: st.session_state.timer_on = st.checkbox(t("timer_enable"), value=st.session_state.timer_on)
    with oc3: st.session_state.perq_seconds = st.number_input(t("duration_seconds"), min_value=2, max_value=60, value=st.session_state.perq_seconds, step=1)

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button(t("start_quiz"), use_container_width=True): start_quiz()
    with bc2:
        if st.button(t("retry_mistakes"), use_container_width=True):
            errs = st.session_state.errors
            if not errs:
                st.warning(t("no_mistakes"))
            else:
                pool = [e for e in errs if not e.get("resolved")] or errs[:]
                qs = [{"a": e["a"], "b": e["b"], "answer": e["correct_answer"]} for e in pool]
                random.shuffle(qs)
                st.session_state.questions = qs
                st.session_state.q_idx = 0; st.session_state.correct = 0
                st.session_state.feedback = ""; st.session_state.pending_next=False
                st.session_state.in_quiz = True
                st.session_state.deadline = (time.time() + st.session_state.perq_seconds) if st.session_state.timer_on else None
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------- GAMEPLAY ----------------------
    if st.session_state.in_quiz and st.session_state.questions:
        q = st.session_state.questions[st.session_state.q_idx]
        total = len(st.session_state.questions)

        # Live auto-refresh (1s) while counting down
        if HAVE_AUTOREFRESH and st.session_state.timer_on and not st.session_state.pending_next:
            st_autorefresh(interval=1000, key="auto_timer")

        # Show feedback pause before next
        if st.session_state.pending_next:
            st.markdown(f"### {st.session_state.feedback}")
            if time.time() >= st.session_state.next_time:
                st.session_state.pending_next = False
                if st.session_state.timer_on:
                    st.session_state.deadline = time.time() + st.session_state.perq_seconds
                st.rerun()

        # Progress header + bar
        st.markdown(
            f"**{t('question')} {st.session_state.q_idx+1}/{total}**  |  "
            f"**{t('correct')}: {st.session_state.correct}**"
        )
        st.progress((st.session_state.q_idx)/max(1,total))

        # Big centered question
        st.markdown(f"<h2 style='text-align:center'>{q['a']} × {q['b']} = ?</h2>", unsafe_allow_html=True)

        # Timer
        if st.session_state.timer_on and not st.session_state.pending_next:
            remaining = int(st.session_state.deadline - time.time())
            if remaining <= 0:
                add_error(q["a"], q["b"], q["answer"], None, "timeout")
                update_table_stats(q["a"], ok=False)
                st.session_state.feedback = f"{t('too_slow')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                st.session_state.q_idx += 1
                if st.session_state.q_idx >= total:
                    end_quiz()
                else:
                    st.session_state.pending_next=True
                    st.session_state.next_time=time.time()+1.0
                st.rerun()
            st.info(f"⏳ {remaining}s")
            st.progress(max(0, min(1, remaining / max(1, st.session_state.perq_seconds))))

        # Keyboard mode (quiz-style with Enter)
        if st.session_state.keyboard_mode and not st.session_state.pending_next:
            st.markdown(f"<div class='quiz-label'>{t('enter_answer')} 👇</div>", unsafe_allow_html=True)
            with st.form(key="answer_form", clear_on_submit=True):
                ans = st.text_input("", key="answer_text", max_chars=5, placeholder="...", label_visibility="collapsed")
                submit = st.form_submit_button(t("submit"))
            # Autofocus input
            components.html("""
                <script>
                const el = window.parent.document.querySelector('input[type="text"][aria-label="answer_text"]')
                          || window.parent.document.querySelector('input[data-testid="stTextInput"]');
                if (el){ el.focus(); el.select && el.select(); }
                </script>
            """, height=0)
            if submit:
                if ans.strip().isdigit():
                    val = int(ans.strip())
                    ok = (val == q["answer"])
                    update_table_stats(q["a"], ok)
                    if ok:
                        st.session_state.correct += 1
                        st.session_state.feedback = f"{t('bravo')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                    else:
                        st.session_state.feedback = f"{t('oops')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                        add_error(q["a"], q["b"], q["answer"], val, "wrong")
                    st.session_state.q_idx += 1
                    if st.session_state.q_idx >= total:
                        end_quiz()
                    else:
                        st.session_state.pending_next=True
                        st.session_state.next_time=time.time()+1.0
                    st.rerun()
                else:
                    st.warning(t("enter_answer"))

        # Multiple choice mode
        if (not st.session_state.keyboard_mode) and (not st.session_state.pending_next):
            correct = q["answer"]
            opts = {correct}
            while len(opts) < 4:
                delta = random.choice([-12,-9,-6,-4,-3,-2,-1,1,2,3,4,6,9,12])
                cand = max(0, correct + delta)
                if random.random() < 0.25:
                    cand = (q["a"] + random.choice([-1,1])) * q["b"]
                    if cand < 0: cand = 0
                opts.add(cand)
            opts = list(opts); random.shuffle(opts)
            cA, cB = st.columns(2)
            clicked = None
            if cA.button(str(opts[0]), use_container_width=True): clicked = opts[0]
            if cB.button(str(opts[1]), use_container_width=True): clicked = opts[1]
            if cA.button(str(opts[2]), use_container_width=True): clicked = opts[2]
            if cB.button(str(opts[3]), use_container_width=True): clicked = opts[3]
            if clicked is not None:
                ok = (clicked == correct)
                update_table_stats(q["a"], ok)
                if ok:
                    st.session_state.correct += 1
                    st.session_state.feedback = f"{t('bravo')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                else:
                    st.session_state.feedback = f"{t('oops')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                    add_error(q["a"], q["b"], q["answer"], clicked, "wrong")
                st.session_state.q_idx += 1
                if st.session_state.q_idx >= total:
                    end_quiz()
                else:
                    st.session_state.pending_next=True
                    st.session_state.next_time=time.time()+1.0
                st.rerun()

    if st.session_state.timer_on and not HAVE_AUTOREFRESH:
        st.caption("ℹ️ " + t("timer_note"))

# ---------------------- PARENT VIEW ----------------------
if st.session_state.view == "parent":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(t("parents_zone"))

    st.markdown(f"**{t('review_mistakes')}**")
    if st.session_state.errors:
        df = pd.DataFrame(st.session_state.errors)
        df_view = df.copy()
        df_view["question"] = df_view["a"].astype(str) + " × " + df_view["b"].astype(str)
        df_view["timestamp"] = pd.to_datetime(df_view["ts"], unit="s")
        df_view = df_view[["timestamp","a","b","question","correct_answer","user_answer","outcome","resolved"]]
        st.dataframe(df_view, use_container_width=True, height=280)
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(t("export_csv"), data=csv_bytes, file_name="multiplication_errors.csv", mime="text/csv")
    else:
        st.info(t("no_mistakes"))

    st.divider()
    st.markdown(f"**{t('progress_chart')}**")
    rows = []
    for k, v in sorted(st.session_state.tables_stats.items(), key=lambda kv:int(kv[0])):
        a = v["attempts"]; c = v["correct"]
        acc = 0 if a==0 else 100*c/a
        rows.append({"table": int(k), "accuracy": acc})
    if rows:
        st.bar_chart(pd.DataFrame(rows).set_index("table"))
    else:
        st.info("No data yet." if st.session_state.lang=="en" else "Pas encore de données.")

    st.divider()
    st.markdown(f"**{t('per_table_summary')}**")
    if st.session_state.tables_stats:
        cols = st.columns(13)
        for i in range(13):
            v = st.session_state.tables_stats.get(i, {"attempts":0,"correct":0})
            cols[i].metric(str(i), f"{v['correct']}/{v['attempts']}")
    else:
        st.info("No attempts yet." if st.session_state.lang=="en" else "Aucune tentative pour l’instant.")

    if st.button(t("reset_all")):
        lang_keep = st.session_state.lang
        st.session_state.clear(); init_state()
        st.session_state.lang = lang_keep
        st.success("Reset done." if lang_keep=="en" else "Réinitialisation effectuée.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- FOOTER ----------------------
st.markdown("<div class='footer'>"+STR[st.session_state.lang]["footer"]+"</div>", unsafe_allow_html=True)
