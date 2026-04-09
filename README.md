# DocBook+ | Clinical Intelligence

<div align="center">
  <h3>AI-Powered Multidisciplinary Medical Diagnostics</h3>
  <p>A sophisticated Streamlit web application demonstrating collaborative AI reasoning in the healthcare domain, powered by ultra-fast LLaMA models and live medical literature retrieval.</p>
</div>

---

## 🧠 Core Architecture

**DocBook+** moves beyond relying on single-model responses, deploying a **coordinated, multi-perspective AI system**. This architecture decomposes complex medical reasoning into parallel, specialized expert workflows. 

When a patient's case is submitted, multiple specialized AI agents run concurrently using ThreadPool execution, each analyzing the data from their unique medical discipline and fetching live contextual references. Their insights are subsequently aggregated by a synthesizer agent into a final multidisciplinary diagnosis.

⚠️ **Disclaimer**: This software is for demonstration and research purposes only. It is **not intended for clinical use**.

---

## ✨ Features

- **Multi-Agent Simulation**: Seamless integration of 6 concurrent specialist models (Cardiologist, Psychologist, Pulmonologist, Neurologist, Endocrinologist, Immunologist).
- **Live PubMed RAG Integration**: Agents dynamically query the NCBI **PubMed E-utilities API** for up-to-date medical abstracts to context-anchor their analyses and provide source citations.
- **Ultra-Fast LLM Backend**: Powered by **Groq** using `llama-3.3-70b-versatile` via Langchain to facilitate rapid, massively parallel token generation.
- **Beautiful Glassmorphic UI**: Fully custom-built Streamlit interface featuring a premium dark theme, frosted glass panels, and floating avatar interactions.
- **Local JSON Database**: Patient histories, diagnostic outputs, and credentials are intentionally handled via lightweight local JSON repositories (`data/users.json`) simulating secure local Electronic Medical Records (EMR) caching without external databases.

---

## ⚡ Quickstart

1. **Set up the environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys:**
   Create a file named `apikey.env` in the root directory and add your Groq provider credentials:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Launch the Web App:**
   ```bash
   streamlit run app.py
   ```
   *The application will automatically launch on `http://localhost:8501/`.*

---

## 🔮 Future Roadmap

- **Vision Modality**: Integration of vision-language models (VLMs) to process raw radiology scans and MRI results directly in the dashboard.
- **Local Sandbox Execution**: Deploy smaller edge-native LLMs directly on-device using llama.cpp or Ollama for absolute privacy-compliant report processing.
- **Dynamic EHR Integrations**: Secure fetching of Electronic Health Records via FHIR standards for automated context generation.
