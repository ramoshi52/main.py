import streamlit as st
import json
import random
import re
import google.generativeai as genai
from google.genai import types

st.set_page_config(page_title="AI English Teacher", page_icon="🇬🇧")

TOPIC_LIST = [
    "🎯 Rastgele Konu",
    "🌍 Travel (Seyahat)",
    "📜 History (Tarih)",
    "🌐 Geography (Coğrafya)",
    "💻 Technology (Teknoloji)",
    "🏥 Medicine (Tıp)",
    "🔬 Science (Bilim)",
    "🎨 Art (Sanat)",
    "⚽ Sports (Spor)",
    "🍕 Food (Yemek)",
    "🌿 Environment (Çevre)",
    "💼 Business (İş)",
    "📚 Education (Eğitim)",
    "🎵 Music (Müzik)",
    "🐾 Animals (Hayvanlar)",
    "🚀 Space (Uzay)",
    "🧠 Psychology (Psikoloji)",
    "💰 Finance (Finans)",
    "✍️ Özel Konu Yaz"
]

TEST_TYPES = [
    "📖 Reading Comprehension",
    "📝 Cloze Test",
    "📚 Vocabulary",
    "✏️ Grammar",
    "🔍 Error Correction",
    "🔄 Paraphrasing",
    "📐 Sentence Completion",
    "🔗 Collocations",
    "💬 Idioms",
    "🔠 Word Formation",
    "📍 Prepositions",
    "✅ True/False"
]

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "show_results" not in st.session_state:
    st.session_state.show_results = False

st.title("🇬🇧 AI English Test Generator")

with st.sidebar:
    st.header("⚙️ Ayarlar")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    
    test_type = st.selectbox("Test Türü", TEST_TYPES)
    level = st.select_slider("Seviye", options=["A1", "A2", "B1", "B2", "C1", "C2"], value="B1")
    
    st.divider()
    selected_topic = st.selectbox("Konu", TOPIC_LIST)
    
    custom_topic = ""
    if selected_topic == "✍️ Özel Konu Yaz":
        custom_topic = st.text_input("Konunuzu yazın")
    
    if selected_topic == "🎯 Rastgele Konu":
        final_topic = ""
    elif selected_topic == "✍️ Özel Konu Yaz":
        final_topic = custom_topic
    else:
        final_topic = selected_topic.split("(")[0].split(" ", 1)[1].strip() if "(" in selected_topic else selected_topic
    
    st.divider()
    word_count = st.slider("Kelime Sayısı", 100, 400, 200, 50)
    question_count = st.selectbox("Soru Sayısı", [5, 10, 15], index=1)

def parse_json_safely(text):
    text = text.strip()
    
    for prefix in ["```json", "```JSON", "```"]:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end+1]
    
    data = json.loads(text)
    return data

def create_prompt(test_type, level, topic, word_count, q_count):
    topic_str = topic if topic else "an interesting topic"
    uid = random.randint(1000, 9999)
    
    type_name = test_type.split(" ", 1)[1] if " " in test_type else test_type
    
    prompt = f"""Create a {level} level {type_name} test about {topic_str}.

RULES:
- Write approximately {word_count} words passage in academic English
- Create exactly {q_count} multiple choice questions  
- Each question needs 4 options: A, B, C, D
- correct_answer field must contain ONLY one letter (A, B, C, or D)
- Make unique content (ID:{uid})

Return ONLY this JSON format, no other text:

{{"passage": "Your academic passage here...", "questions": [{{"id": 1, "question": "What is...?", "options": ["A) first", "B) second", "C) third", "D) fourth"], "correct_answer": "B", "explanation": "Because..."}}]}}"""
    
    return prompt

def call_api(api_key, prompt):
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction="Return only valid JSON. No markdown. No explanation.",
                temperature=0.7
            )
        )
        
        if response.text:
            data = parse_json_safely(response.text)
            
            if "questions" in data and len(data["questions"]) > 0:
                for i, q in enumerate(data["questions"]):
                    if "id" not in q:
                        q["id"] = i + 1
                    if "correct_answer" in q:
                        ans = str(q["correct_answer"]).strip().upper()
                        q["correct_answer"] = ans[0] if ans else "A"
                
                if "passage" not in data:
                    data["passage"] = ""
                    
                return {"ok": True, "data": data}
            else:
                return {"ok": False, "error": "Sorular oluşturulamadı"}
        else:
            return {"ok": False, "error": "Boş yanıt"}
            
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON hatası - Tekrar deneyin"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}

def reset():
    st.session_state.quiz_data = None
    st.session_state.user_answers = {}
    st.session_state.show_results = False

c1, c2 = st.columns([3, 1])
with c1:
    btn_create = st.button("🚀 Testi Oluştur", type="primary", use_container_width=True)
with c2:
    if st.session_state.quiz_data:
        if st.button("🔄 Sıfırla", use_container_width=True):
            reset()
            st.rerun()

if btn_create:
    if not api_key:
        st.warning("Lütfen API anahtarınızı girin.")
    else:
        reset()
        with st.spinner("Test oluşturuluyor..."):
            prompt = create_prompt(test_type, level, final_topic, word_count, question_count)
            result = call_api(api_key, prompt)
            
            if result["ok"]:
                st.session_state.quiz_data = result["data"]
                st.success("Test hazır!")
            else:
                st.error(result["error"])

if st.session_state.quiz_data:
    data = st.session_state.quiz_data
    
    passage = data.get("passage", "")
    if passage and len(passage) > 20:
        st.subheader("📖 Metin")
        st.markdown(passage)
        st.divider()
    
    questions = data.get("questions", [])
    
    if questions:
        st.subheader(f"📝 Sorular ({len(questions)} adet)")
        
        for q in questions:
            qid = q.get("id", 1)
            qtext = q.get("question", "")
            opts = q.get("options", [])
            correct = str(q.get("correct_answer", "A")).strip().upper()
            if len(correct) > 1:
                correct = correct[0]
            expl = q.get("explanation", "")
            
            key = f"q{qid}"
            
            if st.session_state.show_results:
                user_ans = st.session_state.user_answers.get(key, "")
                is_ok = (user_ans == correct)
                
                icon = "✅" if is_ok else "❌"
                st.markdown(f"**{icon} Soru {qid}:** {qtext}")
                
                for opt in opts:
                    letter = opt[0].upper() if opt else ""
                    if letter == correct:
                        st.success(f"✓ {opt}")
                    elif letter == user_ans and not is_ok:
                        st.error(f"✗ {opt}")
                    else:
                        st.write(f"  {opt}")
                
                if expl:
                    with st.expander("Açıklama"):
                        st.write(expl)
            else:
                st.markdown(f"**Soru {qid}:** {qtext}")
                
                user_current = st.session_state.user_answers.get(key)
                idx = None
                if user_current and opts:
                    for i, o in enumerate(opts):
                        if o and o[0].upper() == user_current:
                            idx = i
                            break
                
                choice = st.radio(
                    "Seçiminiz:",
                    opts,
                    index=idx,
                    key=f"radio_{qid}",
                    label_visibility="collapsed"
                )
                
                if choice:
                    st.session_state.user_answers[key] = choice[0].upper()
            
            st.markdown("---")
        
        if not st.session_state.show_results:
            answered = len(st.session_state.user_answers)
            total = len(questions)
            st.progress(answered / total if total > 0 else 0)
            st.write(f"Cevaplanan: {answered}/{total}")
            
            if st.button("✔️ Testi Bitir", type="primary", use_container_width=True):
                st.session_state.show_results = True
                st.rerun()
        else:
            correct_cnt = 0
            total_cnt = len(questions)
            
            for q in questions:
                qid = q.get("id", 1)
                correct = str(q.get("correct_answer", "")).strip().upper()
                if len(correct) > 1:
                    correct = correct[0]
                user_ans = st.session_state.user_answers.get(f"q{qid}", "")
                if user_ans == correct:
                    correct_cnt += 1
            
            pct = (correct_cnt / total_cnt * 100) if total_cnt > 0 else 0
            
            st.subheader("📊 Sonuç")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Doğru", correct_cnt)
            col2.metric("Yanlış", total_cnt - correct_cnt)
            col3.metric("Başarı", f"%{pct:.0f}")
            
            if pct >= 80:
                st.success("🎉 Harika!")
            elif pct >= 60:
                st.info("👍 İyi!")
            elif pct >= 40:
                st.warning("📚 Daha fazla çalış!")
            else:
                st.error("📖 Tekrar dene!")
            
            if st.button("🔁 Tekrar Çöz", use_container_width=True):
                st.session_state.user_answers = {}
                st.session_state.show_results = False
                st.rerun()
    else:
        st.warning("Sorular yüklenemedi. Lütfen tekrar deneyin.")

st.markdown("---")
st.caption("AI English Test Generator")
