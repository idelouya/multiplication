import time
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Multiplication Trainer", page_icon="🧮", layout="centered")

# ------------------ i18n ------------------
STR = {
    "fr": {
        "title": "Multiplication Trainer",
        "lang_fr": "Français",
        "lang_en": "English",
        "tab_child": "Enfant",
        "tab_parent": "Parent",

        "kids_zone": "Espace Enfant",
        "parents_zone": "Espace Parent",
        "tables_label": "Tables de multiplication (0 à 12)",
        "keyboard_mode": "✏️ Entrer la réponse au clavier",
        "timer_enable": "⏳ Activer le chrono par question",
        "duration_seconds": "Durée (secondes)",
        "start_quiz": "▶ Démarrer le quiz",
        "retry_mistakes": "🔁 Rejouer mes erreurs",
        "question": "Question",
        "correct": "Correct",
        "enter_answer": "Tape ta réponse au clavier :",
        "submit": "Valider",
        "too_slow": "⏳ Trop lent !",
        "oops": "❌ Oups",
        "bravo": "✅ Bravo !",
        "finished": "Terminé !",
        "badge_mastered": "🏅 Maîtrisé !",
        "badge_almost": "⭐ Presque parfait !",
        "badge_keep": "💪 Continue d'essayer !",
        "results_fmt": "Résultats : {correct}/{total} ({percent}%).",
        "no_tables": "Choisis au moins une table.",
        "no_mistakes": "Aucune erreur enregistrée pour le moment.",
        "review_mistakes": "📄 Voir erreurs",
        "progress_chart": "📊 Graphique de progrès",
        "export_csv": "💾 Télécharger erreurs (CSV)",
        "reset_all": "♻ Réinitialiser tout",
        "per_table_summary": "Progrès par table (correct / essais)",
        "footer": "© 2025 Multiplication Trainer – Développé par Illan Delouya",
    },
    "en": {
        "title": "Multiplication Trainer",
        "lang_fr": "French",
        "lang_en": "English",
        "tab_child": "Kids",
        "tab_parent": "Parent",

        "kids_zone": "Kids Zone",
        "parents_zone": "Parents’ Zone",
        "tables_label": "Times tables (0 to 12)",
        "keyboard_mode": "✏️ Type answer with keyboard",
        "timer_enable": "⏳ Enable per-question timer",
        "duration_seconds": "Duration (seconds)",
        "start_quiz": "▶ Start quiz",
        "retry_mistakes": "🔁 Retry mistakes",
        "question": "Question",
        "correct": "Correct",
        "enter_answer": "Type your answer:",
        "submit": "Submit",
        "too_slow": "⏳ Too slow!",
        "oops": "❌ Oops",
        "bravo": "✅ Great job!",
        "finished": "Finished!",
        "badge_mastered": "🏅 Mastered!",
        "badge_almost": "⭐ Almost perfect!",
        "badge_keep": "💪 Keep practicing!",
        "results_fmt": "Results: {correct}/{total} ({percent}%).",
        "no_tables": "Please select at least one table.",
        "no_mistakes": "No mistakes recorded yet.",
        "review_mistakes": "📄 Review mistakes",
        "progress_chart": "📊 Progress chart",
        "export_csv": "💾 Download errors (CSV)",
        "reset_all": "♻ Reset all",
        "per_table_summary": "Progress by table (correct / attempts)",
        "footer": "© 2025 Multiplication Trainer – Developed by Illan Delouya",
    },
}

# ------------------ Session state helpers ------------------
def init_state():
    ss = st.session_state
    ss.setdefault("lang", "fr")
    ss.setdefault("selected_tables", [0,1,2,3])
    ss.setdefault("keyboard_mode", True)
    ss.setdefault("timer_on", True)
    ss.setdefault("perq_seconds", 8)

    # quiz state
    ss.setdefault("in_quiz", False)
    ss.setdefault("retry_mode", False)
    ss.setdefault("questions", [])     # list of dicts: {"a":..,"b":..,"answer":..}
    ss.setdefault("q_idx", 0)
    ss.setdefault("correct", 0)
    ss.setdefault("deadline", None)    # timestamp for timer
    ss.setdefault("feedback", "")      # bravo / oops / too slow text

    # data store (lives in memory for Streamlit session)
    ss.setdefault("tables_stats", {})  # {table: {"attempts": int, "correct": int}}
    ss.setdefault("errors", [])        # list of dicts: {ts,a,b,correct_answer,user_answer,outcome,resolved}

def t(key):
    return STR[st.session_state.lang][key]

init_state()

# ------------------ Language selector (top row) ------------------
colL, colR = st.columns([1,1])
with colL:
    st.markdown(f"## 🧮 {t('title')}")
with colR:
    c1, c2 = st.columns(2)
    with c1:
        if st.button(STR["fr"]["lang_fr"] if st.session_state.lang=="en" else f"**{STR['fr']['lang_fr']}**", use_container_width=True):
            st.session_state.lang = "fr"
            st.rerun()
    with c2:
        if st.button(STR["en"]["lang_en"] if st.session_state.lang=="fr" else f"**{STR['en']['lang_en']}**", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()

st.markdown("---")

# ------------------ Helpers ------------------
def build_questions_from_tables(tables):
    qs = []
    for a in tables:
        for b in range(1, 13):
            qs.append({"a": a, "b": b, "answer": a*b})
    random.shuffle(qs)
    return qs

def build_questions_from_errors(errors):
    pool = [e for e in errors if not e.get("resolved")]
    if not pool:
        pool = errors[:]  # fallback to all if none unresolved
    qs = [{"a": e["a"], "b": e["b"], "answer": e["correct_answer"]} for e in pool]
    random.shuffle(qs)
    return qs

def update_table_stats(a_table, ok):
    stats = st.session_state.tables_stats.setdefault(a_table, {"attempts":0, "correct":0})
    stats["attempts"] += 1
    if ok:
        stats["correct"] += 1

def add_error(a, b, correct_answer, user_answer, outcome):
    st.session_state.errors.append({
        "ts": int(time.time()),
        "a": int(a),
        "b": int(b),
        "correct_answer": int(correct_answer),
        "user_answer": (None if user_answer is None else int(user_answer)),
        "outcome": outcome,  # "wrong" or "timeout"
        "resolved": False,
    })

def resolve_error(a,b):
    for e in st.session_state.errors:
        if not e.get("resolved") and e["a"]==a and e["b"]==b:
            e["resolved"] = True
            return

def start_quiz(retry=False):
    ss = st.session_state
    if retry:
        if not ss.errors:
            st.warning(t("no_mistakes"))
            return
        ss.questions = build_questions_from_errors(ss.errors)
        ss.retry_mode = True
    else:
        if not ss.selected_tables:
            st.warning(t("no_tables"))
            return
        ss.questions = build_questions_from_tables(ss.selected_tables)
        ss.retry_mode = False

    ss.q_idx = 0
    ss.correct = 0
    ss.feedback = ""
    ss.in_quiz = True
    ss.deadline = (time.time() + ss.perq_seconds) if ss.timer_on else None
    st.rerun()

def end_quiz():
    ss = st.session_state
    total = len(ss.questions)
    correct = ss.correct
    percent = round(100*correct/max(1,total))
    if percent == 100:
        badge = t("badge_mastered")
    elif percent >= 85:
        badge = t("badge_almost")
    else:
        badge = t("badge_keep")
    st.success(f"**{t('finished')}**\n\n{badge}\n\n" + t("results_fmt").format(correct=correct, total=total, percent=percent))
    ss.in_quiz = False
    ss.retry_mode = False
    ss.questions = []
    ss.q_idx = 0
    ss.correct = 0
    ss.deadline = None
    ss.feedback = ""

def show_progress_chart():
    # build DataFrame from tables_stats
    rows = []
    for k, v in sorted(st.session_state.tables_stats.items(), key=lambda kv:int(kv[0])):
        a = v["attempts"]; c = v["correct"]
        acc = 0 if a==0 else 100*c/a
        rows.append({"table": int(k), "accuracy": acc})
    if not rows:
        st.info(t("no_mistakes") if st.session_state.lang=="fr" else "No data yet.")
        return
    df = pd.DataFrame(rows)
    st.bar_chart(df.set_index("table"))

# ------------------ Tabs ------------------
tab_child, tab_parent = st.tabs([f"🧒 {t('tab_child')}", f"👨‍👩‍👧 {t('tab_parent')}"])

with tab_child:
    st.subheader(t("kids_zone"))

    # Tables selection
    st.caption(t("tables_label"))
    cols = st.columns(7)
    selected = []
    for i in range(13):
        c = cols[i%7]
        with c:
            if st.checkbox(str(i), value=(i in st.session_state.selected_tables), key=f"table_{i}"):
                selected.append(i)
    st.session_state.selected_tables = selected

    # Options
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        st.session_state.keyboard_mode = st.checkbox(t("keyboard_mode"), value=st.session_state.keyboard_mode)
    with c2:
        st.session_state.timer_on = st.checkbox(t("timer_enable"), value=st.session_state.timer_on)
    with c3:
        st.session_state.perq_seconds = st.number_input(t("duration_seconds"), min_value=2, max_value=60, value=st.session_state.perq_seconds, step=1)

    # Actions
    a1, a2 = st.columns(2)
    with a1:
        if st.button(t("start_quiz"), use_container_width=True):
            start_quiz(retry=False)
    with a2:
        if st.button(t("retry_mistakes"), use_container_width=True):
            start_quiz(retry=True)

    st.divider()

    # Gameplay UI (renders here while in_quiz)
    if st.session_state.in_quiz and st.session_state.questions:
        q = st.session_state.questions[st.session_state.q_idx]
        total = len(st.session_state.questions)
        st.markdown(f"**{t('question')} {st.session_state.q_idx+1}/{total}**  |  **{t('correct')}: {st.session_state.correct}**")
        st.markdown(f"## **{q['a']} × {q['b']} = ?**")

        # Timer (countdown)
        if st.session_state.timer_on:
            remaining = int(st.session_state.deadline - time.time())
            if remaining <= 0:
                # timeout
                add_error(q["a"], q["b"], q["answer"], None, "timeout")
                update_table_stats(q["a"], ok=False)
                st.session_state.feedback = f"{t('too_slow')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                # move next
                st.session_state.q_idx += 1
                if st.session_state.q_idx >= total:
                    end_quiz()
                else:
                    st.session_state.deadline = time.time() + st.session_state.perq_seconds
                st.rerun()
            st.progress(max(0, min(1, remaining / max(1, st.session_state.perq_seconds))))
            st.info(f"⏳ {remaining}s")

        # Answer input
        if st.session_state.keyboard_mode:
            ans = st.text_input(t("enter_answer"), key="answer_text", value="", max_chars=4)
            go = st.button(t("submit"))
            if go:
                if ans.strip().isdigit():
                    val = int(ans.strip())
                    ok = (val == q["answer"])
                    update_table_stats(q["a"], ok)
                    if ok:
                        st.session_state.correct += 1
                        st.session_state.feedback = f"{t('bravo')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                        if st.session_state.retry_mode:
                            resolve_error(q["a"], q["b"])
                    else:
                        st.session_state.feedback = f"{t('oops')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                        add_error(q["a"], q["b"], q["answer"], val, "wrong")

                    # advance
                    st.session_state.q_idx += 1
                    if st.session_state.q_idx >= total:
                        end_quiz()
                    else:
                        if st.session_state.timer_on:
                            st.session_state.deadline = time.time() + st.session_state.perq_seconds
                    st.rerun()
                else:
                    st.warning(t("enter_answer"))
        else:
            # Multiple-choice: generate 4 options
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

            c1, c2 = st.columns(2)
            clicked_value = None
            if c1.button(str(opts[0]), use_container_width=True): clicked_value = opts[0]
            if c2.button(str(opts[1]), use_container_width=True): clicked_value = opts[1]
            if c1.button(str(opts[2]), use_container_width=True): clicked_value = opts[2]
            if c2.button(str(opts[3]), use_container_width=True): clicked_value = opts[3]

            if clicked_value is not None:
                ok = (clicked_value == correct)
                update_table_stats(q["a"], ok)
                if ok:
                    st.session_state.correct += 1
                    st.session_state.feedback = f"{t('bravo')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                    if st.session_state.retry_mode:
                        resolve_error(q["a"], q["b"])
                else:
                    st.session_state.feedback = f"{t('oops')}  \n**{q['a']} × {q['b']} = {q['answer']}**"
                    add_error(q["a"], q["b"], q["answer"], clicked_value, "wrong")

                # advance
                st.session_state.q_idx += 1
                if st.session_state.q_idx >= total:
                    end_quiz()
                else:
                    if st.session_state.timer_on:
                        st.session_state.deadline = time.time() + st.session_state.perq_seconds
                st.rerun()

        # Feedback banner
        if st.session_state.feedback:
            st.markdown(f"### {st.session_state.feedback}")

with tab_parent:
    st.subheader(t("parents_zone"))

    # Mistakes table
    st.markdown(f"**{t('review_mistakes')}**")
    if st.session_state.errors:
        df = pd.DataFrame(st.session_state.errors)
        df_view = df.copy()
        df_view["question"] = df_view["a"].astype(str) + " x " + df_view["b"].astype(str)
        df_view["timestamp"] = pd.to_datetime(df_view["ts"], unit="s")
        df_view = df_view[["timestamp", "a", "b", "question", "correct_answer", "user_answer", "outcome", "resolved"]]
        st.dataframe(df_view, use_container_width=True, height=260)

        # CSV download
        csv_bytes = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(t("export_csv"), data=csv_bytes, file_name="multiplication_errors.csv", mime="text/csv")
    else:
        st.info(t("no_mistakes"))

    st.divider()

    # Progress chart
    st.markdown(f"**{t('progress_chart')}**")
    show_progress_chart()

    st.divider()

    # Per-table summary labels
    st.markdown(f"**{t('per_table_summary')}**")
    if st.session_state.tables_stats:
        cols = st.columns(13)
        for i in range(13):
            v = st.session_state.tables_stats.get(i, {"attempts":0,"correct":0})
            cols[i].metric(str(i), f"{v['correct']}/{v['attempts']}")
    else:
        st.info(t("no_mistakes") if st.session_state.lang=="fr" else "No attempts yet.")

    # Reset button
    if st.button(t("reset_all")):
        lang_keep = st.session_state.lang
        st.session_state.clear()
        init_state()
        st.session_state.lang = lang_keep
        st.success("Reset done." if lang_keep=="en" else "Réinitialisation effectuée.")
        st.rerun()

# ------------------ Footer ------------------
st.markdown("---")
st.caption(STR[st.session_state.lang]["footer"])
