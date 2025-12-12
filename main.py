from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model loading will be attempted but won't block app startup
print("Loading models...")
tokenizer = None
model = None

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    import os
    
    # Try loading custom model first
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "qgen_model", "flan_t5_qgen_ep6_clean")
    
    try:
        print(f"Loading custom model from {MODEL_DIR}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR, trust_remote_code=True)
        print("✓ Custom model loaded")
    except Exception as custom_err:
        print(f"Custom model load failed: {custom_err}")
        print("Loading standard FLAN-T5 from Hugging Face...")
        
        # Fallback to standard FLAN-T5-base
        tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
        model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
        print("✓ FLAN-T5 model loaded")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"✓ Model on {device}")
    
except Exception as e:
    print(f"⚠ Models not loaded (will use mock responses): {e}")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    prompt: str
    max_tokens: int = 150
    num_questions: int = 5

class InterviewSubmission(BaseModel):
    candidate: Dict[str, str]
    position: str
    ats_score: float
    questions_answers: List[Dict[str, str]]
    timestamp: str

@app.get("/")
def read_root():
    return {"message": "AI Interviewer Backend Running", "status": "ok"}

@app.post("/ats/analyze")
async def analyze_resume(request: dict):
    """Analyze resume against job description"""
    try:
        resume = request.get("resume", "")
        job_description = request.get("job_description", "")
        
        if not resume or not job_description:
            return {"error": "Resume and job description are required", "status": "error"}
        
        # Simple keyword matching ATS scoring
        import re
        
        # Extract keywords (words with 4+ chars)
        resume_words = set(re.findall(r'\b\w{4,}\b', resume.lower()))
        job_words = set(re.findall(r'\b\w{4,}\b', job_description.lower()))
        
        # Calculate match
        matched = resume_words & job_words
        ats_score = int((len(matched) / len(job_words) * 100)) if job_words else 0
        ats_score = min(ats_score, 100)
        
        # Get matched and missing keywords
        important_job_keywords = [w for w in job_description.split() if len(w) > 5]
        matched_keywords = [w for w in important_job_keywords if w.lower() in resume.lower()]
        missing_keywords = [w for w in important_job_keywords if w.lower() not in resume.lower()]
        
        # Determine compatibility
        if ats_score >= 80:
            compatibility = "🟢 Excellent Match"
        elif ats_score >= 60:
            compatibility = "🟡 Good Match"
        elif ats_score >= 40:
            compatibility = "🟠 Fair Match"
        else:
            compatibility = "🔴 Needs Improvement"
        
        # Generate feedback
        feedback = f"Your resume matches {ats_score}% of the job requirements. "
        if missing_keywords:
            feedback += f"Consider adding: {', '.join(missing_keywords[:5])}"
        else:
            feedback += "Great job matching all key requirements!"
        
        return {
            "ats_score": ats_score,
            "matched_keywords": len(matched_keywords),
            "total_keywords": len(important_job_keywords),
            "matched_keywords_list": list(set(matched_keywords))[:15],
            "missing_keywords": list(set(missing_keywords))[:15],
            "compatibility": compatibility,
            "feedback": feedback,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/qgen/generate")
async def generate_questions(request: QuestionRequest):
    """Generate multiple interview questions using FLAN-T5 model"""
    if not model or not tokenizer:
        # Generate mock questions based on user's prompt
        mock_templates = [
            f"What are the key concepts you should understand about {request.prompt}?",
            f"If you were explaining {request.prompt} to a beginner, where would you start?",
            f"Describe a real-world scenario where {request.prompt} would be useful.",
            f"What are common mistakes people make when working with {request.prompt}?",
            f"How would you debug code related to {request.prompt}?",
            f"What are the performance considerations for {request.prompt}?",
            f"Compare and contrast {request.prompt} with similar concepts.",
            f"What tools or libraries are commonly used for {request.prompt}?",
            f"How has {request.prompt} evolved over time?",
            f"What best practices would you follow when implementing {request.prompt}?"
        ]
        return {
            "questions": mock_templates[:request.num_questions],
            "prompt": request.prompt,
            "status": "success_mock",
            "note": "Generated with mock data - ML models not loaded"
        }
    
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        questions = []
        
        # Create prompt template for question generation
        question_prompt = f"Generate a technical interview question about: {request.prompt}"
        
        # Generate multiple questions
        for i in range(request.num_questions):
            # Tokenize input
            inputs = tokenizer(
                question_prompt, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate with the model with varied parameters for diversity
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=min(request.max_tokens + 20, 150),
                    num_beams=2,
                    temperature=0.7 + (i * 0.08),  # Vary temperature for diversity
                    top_p=0.9,
                    do_sample=True,
                    early_stopping=True
                )
            
            # Decode the generated text
            generated_question = tokenizer.decode(outputs[0], skip_special_tokens=True)
            questions.append(generated_question)
        
        return {
            "questions": questions,
            "prompt": request.prompt,
            "status": "success",
            "note": "AI-generated using FLAN-T5 model",
            "count": len(questions)
        }
    
    except Exception as e:
        print(f"Error during generation: {e}")
        return {
            "error": str(e),
            "status": "error"
        }

@app.post("/interview/submit")
async def submit_interview(submission: InterviewSubmission):
    # Save interview results
    print("Interview submitted:", submission.candidate)
    return {"status": "success", "message": "Interview saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)