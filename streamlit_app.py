import streamlit as st
import requests

# Page config
st.set_page_config(
    page_title="Interview Question Generator",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 8px;
    }
    .question-box {
        background-color: #f0f4f8;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #0068c9;
        margin: 1rem 0;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .header-section {
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🎤 Interview Preparation Platform")
st.markdown("Prepare for interviews with AI-powered questions and ATS resume analysis", help="Generate interview questions and analyze your resume against job requirements")

# Sidebar config
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    backend_url = st.text_input(
        "Backend URL",
        value="http://127.0.0.1:8000",
        help="Enter the FastAPI backend URL"
    )
    st.divider()

# Create tabs
tab1, tab2 = st.tabs(["🎤 Question Generator", "📄 ATS Resume Analyzer"])

# ==================== TAB 1: QUESTION GENERATOR ====================
with tab1:
    # Main content area
    col1, col2 = st.columns([2, 1], gap="medium")

with tab1:
    # Main content area
    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        st.markdown("### 📝 Question Parameters")
        
        prompt = st.text_area(
            "📌 Topic/Prompt",
            value="Write a simple Python interview question about lists",
            height=100,
            help="Enter the topic you want interview questions for",
            placeholder="e.g., Python lists, REST APIs, Database design, etc."
        )
        
        # Quick templates
        with st.expander("💡 Quick Templates", expanded=False):
            templates = {
                "Python Basics": "Explain Python data structures and their use cases",
                "Web Development": "Describe how REST APIs work and their best practices",
                "Database Design": "Explain database normalization and indexing strategies",
                "System Design": "How would you design a scalable web application?",
                "Data Science": "Explain machine learning model evaluation metrics"
            }
            
            selected_template = st.selectbox(
                "Choose a template:",
                options=list(templates.keys()),
                label_visibility="collapsed"
            )
            if st.button("Use Template", key="template_btn"):
                prompt = templates[selected_template]
                st.rerun()

    with col2:
        st.markdown("### 🎯 Settings")
        
        num_questions = st.slider(
            "Number of Questions",
            min_value=1,
            max_value=10,
            value=5,
            help="How many questions to generate"
        )
        
        max_tokens = st.slider(
            "Max Question Length",
            min_value=30,
            max_value=500,
            value=60,
            help="Maximum words per question"
        )

    # Generate button
    st.divider()
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        generate_btn = st.button("🚀 Generate Questions", use_container_width=True, type="primary")

    with col_btn2:
        if st.button("🔄 Clear", use_container_width=True, key="clear_questions"):
            st.rerun()

    # Results section
    if generate_btn:
        st.markdown("### 📋 Generated Questions")
        
        with st.spinner("Generating questions..."):
            url = f"{backend_url}/qgen/generate"
            payload = {
                "prompt": prompt,
                "max_new_tokens": max_tokens,
                "num_questions": num_questions
            }
            
            try:
                r = requests.post(url, json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                
                if "questions" in data:
                    questions = data["questions"]
                    
                    # Display questions
                    for i, question in enumerate(questions, 1):
                        st.markdown(
                            f'<div class="question-box"><strong>Q{i}:</strong> {question}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Status indicator
                    col_status1, col_status2 = st.columns([2, 1])
                    with col_status1:
                        if data.get("status") == "success_mock":
                            st.warning(
                                "⚠️ **Models not loaded** — Showing template-based questions (not AI-generated yet). "
                                "To use real AI generation, load the FLAN-T5 model.",
                                icon="⚠️"
                            )
                        else:
                            st.success("✅ AI-generated questions", icon="✅")
                    
                    with col_status2:
                        st.metric("Questions Generated", len(questions))
                
                elif "error" in data:
                    st.error(f"❌ Error: {data['error']}", icon="❌")
                else:
                    st.write(data)
            
            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot connect to backend. Make sure it's running on " + backend_url,
                    icon="❌"
                )
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Try again.", icon="⏱️")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}", icon="❌")

# ==================== TAB 2: ATS RESUME ANALYZER ====================
with tab2:
    st.markdown("### 📄 Resume ATS Analysis")
    st.markdown("Check how well your resume matches job requirements and get ATS score")
    
    col1_ats, col2_ats = st.columns([2, 1], gap="medium")
    
    with col1_ats:
        st.markdown("#### Your Resume")
        
        upload_method = st.radio("Choose input method:", ["📄 Upload File", "📝 Paste Text"], horizontal=True)
        
        resume_text = ""
        if upload_method == "📄 Upload File":
            uploaded_file = st.file_uploader(
                "Upload resume (PDF, TXT, or DOCX)",
                type=["pdf", "txt", "docx"],
                help="Upload your resume file"
            )
            if uploaded_file:
                try:
                    if uploaded_file.type == "text/plain":
                        resume_text = uploaded_file.read().decode("utf-8")
                    elif uploaded_file.type == "application/pdf":
                        try:
                            import PyPDF2
                            pdf_reader = PyPDF2.PdfReader(uploaded_file)
                            resume_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
                        except ImportError:
                            st.warning("PDF support requires: pip install PyPDF2")
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        try:
                            from docx import Document
                            doc = Document(uploaded_file)
                            resume_text = "\n".join([para.text for para in doc.paragraphs])
                        except ImportError:
                            st.warning("DOCX support requires: pip install python-docx")
                    st.success(f"✅ Uploaded: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        else:
            resume_text = st.text_area(
                "Paste your resume text here",
                height=250,
                placeholder="Copy and paste your resume content here...",
                help="Plain text from your resume",
                label_visibility="collapsed"
            )
    
    with col2_ats:
        st.markdown("#### Job Description")
        job_description = st.text_area(
            "Paste job description here",
            height=250,
            placeholder="Copy and paste the job description here...",
            help="The job posting you're applying for",
            label_visibility="collapsed"
        )
    
    st.divider()
    
    col_btn_ats1, col_btn_ats2 = st.columns(2)
    with col_btn_ats1:
        analyze_btn = st.button("🔍 Analyze Resume", use_container_width=True, type="primary")
    with col_btn_ats2:
        if st.button("🔄 Clear", use_container_width=True, key="clear_ats"):
            st.rerun()
    
    if analyze_btn:
        if not resume_text.strip():
            st.error("❌ Please paste your resume text", icon="❌")
        elif not job_description.strip():
            st.error("❌ Please paste the job description", icon="❌")
        else:
            st.markdown("### 📊 ATS Analysis Results")
            
            with st.spinner("🔍 Analyzing resume..."):
                url = f"{backend_url}/ats/analyze"
                payload = {
                    "resume": resume_text,
                    "job_description": job_description
                }
                
                try:
                    r = requests.post(url, json=payload, timeout=60)
                    r.raise_for_status()
                    data = r.json()
                    
                    if "error" not in data:
                        # ATS Score - Large and Eye-Catching
                        score = data.get("ats_score", 0)
                        
                        # Score gauge display
                        if score >= 80:
                            score_color = "🟢"
                            score_status = "EXCELLENT"
                        elif score >= 60:
                            score_color = "🟡"
                            score_status = "GOOD"
                        elif score >= 40:
                            score_color = "🟠"
                            score_status = "FAIR"
                        else:
                            score_color = "🔴"
                            score_status = "NEEDS WORK"
                        
                        # Display main score
                        st.markdown(f"""
<div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 15px; color: white;'>
<h1 style='margin: 0; font-size: 3em;'>{score}%</h1>
<p style='margin: 10px 0 0 0; font-size: 1.5em;'>{score_color} {score_status}</p>
</div>
""", unsafe_allow_html=True)
                        
                        st.divider()
                        
                        # Metrics row
                        col_m1, col_m2, col_m3 = st.columns(3)
                        
                        with col_m1:
                            match_keywords = data.get("matched_keywords", 0)
                            total_keywords = data.get("total_keywords", 1)
                            st.metric("✅ Keywords Matched", f"{match_keywords}/{total_keywords}")
                        
                        with col_m2:
                            compatibility = data.get("compatibility", "Unknown")
                            compat_short = compatibility.split()[1] if len(compatibility.split()) > 1 else compatibility
                            st.metric("🎯 Status", compat_short)
                        
                        with col_m3:
                            match_percent = int((match_keywords / total_keywords * 100)) if total_keywords > 0 else 0
                            st.metric("📈 Coverage", f"{match_percent}%")
                        
                        st.divider()
                        
                        # Matched Keywords
                        matched = data.get("matched_keywords_list", [])
                        if matched:
                            st.markdown("#### ✅ Keywords You Have")
                            # Display as nice badges
                            matched_html = " ".join([f'<span style="display:inline-block; background:#10b981; color:white; padding:8px 12px; margin:4px; border-radius:20px; font-size:0.9em;">{k}</span>' for k in matched[:10]])
                            st.markdown(matched_html, unsafe_allow_html=True)
                        
                        # Missing Keywords
                        missing = data.get("missing_keywords", [])
                        if missing:
                            st.markdown("#### ❌ Keywords to Add (Important!)")
                            # Display as warning badges
                            missing_html = " ".join([f'<span style="display:inline-block; background:#ef4444; color:white; padding:8px 12px; margin:4px; border-radius:20px; font-size:0.9em;">{k}</span>' for k in missing[:10]])
                            st.markdown(missing_html, unsafe_allow_html=True)
                            st.info("💡 Add these keywords to your resume to improve ATS score")
                        else:
                            st.success("✅ Great! Your resume has all key keywords!")
                        
                        st.divider()
                        
                        # Feedback
                        feedback = data.get("feedback", "")
                        if feedback:
                            st.markdown("#### 💼 Recommendations")
                            st.info(feedback)
                    else:
                        st.error(f"❌ Error: {data.get('error', 'Unknown error')}", icon="❌")
                
                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Cannot connect to backend. Make sure it's running on " + backend_url,
                        icon="❌"
                    )
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Try again.", icon="⏱️")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}", icon="❌")

# Footer & Info
st.divider()

with st.expander("❓ Why is FLAN model not loading?", expanded=False):
    st.markdown("""
    The FLAN-T5 model isn't loading due to **tokenizer format incompatibility** with the current transformers version.
    
    **Solutions:**
    
    1. **Option A: Update transformers version**
       ```bash
       pip install transformers --upgrade
       ```
    
    2. **Option B: Regenerate tokenizer with current version**
       ```bash
       from transformers import T5Tokenizer
       tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")
       tokenizer.save_pretrained("./flan_t5_qgen_ep6_clean")
       ```
    
    3. **Option C: Use CPU-compatible FLAN-T5**
       ```bash
       pip install --index-url https://download.pytorch.org/whl/cpu/ torch transformers
       ```
    
    For now, the app uses **mock questions** that are still helpful for practice! 📝
    """)

with st.expander("📦 Optional: File upload support", expanded=False):
    st.markdown("""
    To enable PDF & DOCX resume uploads, install:
    ```bash
    pip install PyPDF2 python-docx
    ```
    
    Then refresh the app. You'll be able to upload:
    - 📄 PDF resumes
    - 📝 Text files (.txt)
    - 📋 Word documents (.docx)
    """)

st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9rem; margin-top: 2rem;'>
    💡 Tip: The more specific your job description, the better the analysis | 🔧 Adjust settings to customize output<br>
    </div>
    """,
    unsafe_allow_html=True
)
