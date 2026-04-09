import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from langchain_groq import ChatGroq
from typing import List, Optional


# ─── PubMed Search Tool ───────────────────────────────────────────────────────

def search_pubmed(query: str, max_results: int = 3) -> List[str]:
    """Search PubMed and return article titles."""
    try:
        encoded_query = urllib.parse.quote(query)
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={encoded_query}&retmax={max_results}&retmode=json"
        )
        with urllib.request.urlopen(search_url, timeout=5) as response:
            search_data = json.loads(response.read().decode())

        ids = search_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        ids_str = ",".join(ids)
        fetch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={ids_str}&rettype=abstract&retmode=xml"
        )
        with urllib.request.urlopen(fetch_url, timeout=5) as response:
            xml_data = response.read().decode()

        root = ET.fromstring(xml_data)
        titles = []
        for article in root.findall(".//ArticleTitle"):
            if article.text:
                titles.append(article.text.strip())
        return titles[:max_results]

    except Exception:
        return []


# ─── Prompts ──────────────────────────────────────────────────────────────────

AGENT_PROMPTS = {
    "Cardiologist": """
You are an expert cardiologist. Analyze the patient medical report below.
Focus on: cardiac issues, arrhythmias, structural abnormalities, blood pressure, ECG findings.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "possible_conditions": ["condition1", "condition2"],
    "reasoning": "your clinical reasoning",
    "recommended_tests": ["test1", "test2"],
    "urgency": "low|moderate|high|critical",
    "pubmed_references": []
}}

Medical Report:
{medical_report}

Relevant PubMed Literature:
{pubmed_context}
""",
    "Psychologist": """
You are an expert psychologist. Analyze the patient report below.
Focus on: mental health conditions, anxiety, depression, trauma, behavioral patterns.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "possible_conditions": ["condition1", "condition2"],
    "reasoning": "your clinical reasoning",
    "recommended_tests": ["test1", "test2"],
    "urgency": "low|moderate|high|critical",
    "pubmed_references": []
}}

Patient Report:
{medical_report}

Relevant PubMed Literature:
{pubmed_context}
""",
    "Pulmonologist": """
You are an expert pulmonologist. Analyze the patient report below.
Focus on: respiratory conditions, asthma, COPD, breathing disorders, lung function.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "possible_conditions": ["condition1", "condition2"],
    "reasoning": "your clinical reasoning",
    "recommended_tests": ["test1", "test2"],
    "urgency": "low|moderate|high|critical",
    "pubmed_references": []
}}

Patient Report:
{medical_report}

Relevant PubMed Literature:
{pubmed_context}
""",
    "Neurologist": """
You are an expert neurologist. Analyze the patient report below.
Focus on: neurological conditions, migraines, epilepsy, neuropathy, cognitive/memory disorders.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "possible_conditions": ["condition1", "condition2"],
    "reasoning": "your clinical reasoning",
    "recommended_tests": ["test1", "test2"],
    "urgency": "low|moderate|high|critical",
    "pubmed_references": []
}}

Patient Report:
{medical_report}

Relevant PubMed Literature:
{pubmed_context}
""",
    "Endocrinologist": """
You are an expert endocrinologist. Analyze the patient report below.
Focus on: hormonal disorders, diabetes, thyroid dysfunction, adrenal issues, metabolic conditions.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "possible_conditions": ["condition1", "condition2"],
    "reasoning": "your clinical reasoning",
    "recommended_tests": ["test1", "test2"],
    "urgency": "low|moderate|high|critical",
    "pubmed_references": []
}}

Patient Report:
{medical_report}

Relevant PubMed Literature:
{pubmed_context}
""",
    "Immunologist": """
You are an expert immunologist. Analyze the patient report below.
Focus on: autoimmune conditions, allergies, immune deficiencies, inflammatory disorders.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "possible_conditions": ["condition1", "condition2"],
    "reasoning": "your clinical reasoning",
    "recommended_tests": ["test1", "test2"],
    "urgency": "low|moderate|high|critical",
    "pubmed_references": []
}}

Patient Report:
{medical_report}

Relevant PubMed Literature:
{pubmed_context}
"""
}

PUBMED_QUERIES = {
    "Cardiologist": "cardiac arrhythmia diagnosis treatment",
    "Psychologist": "anxiety disorder panic attack treatment",
    "Pulmonologist": "respiratory breathing disorder diagnosis",
    "Neurologist": "neurological cognitive memory disorder diagnosis",
    "Endocrinologist": "endocrine hormonal metabolic disorder diagnosis",
    "Immunologist": "autoimmune inflammatory disorder diagnosis treatment",
}


# ─── Base Agent ───────────────────────────────────────────────────────────────

class Agent:
    def __init__(self, medical_report=None, role=None, extra_info=None):
        self.medical_report = medical_report
        self.role = role
        self.extra_info = extra_info
        self.model = ChatGroq(temperature=0, model="llama-3.3-70b-versatile")

    def fetch_pubmed_context(self) -> str:
        query = PUBMED_QUERIES.get(self.role, self.role)
        titles = search_pubmed(query)
        if not titles:
            return "No PubMed references found."
        return "\n".join(f"- {t}" for t in titles)

    def parse_json_response(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {
                "possible_conditions": ["Unable to parse structured output"],
                "reasoning": text,
                "recommended_tests": [],
                "urgency": "unknown",
                "pubmed_references": []
            }

    def run(self) -> dict:
        print(f"{self.role} is running...")
        try:
            if self.role == "MultidisciplinaryTeam":
                reports_section = "\n\n".join([
                    f"### {specialist}:\n{json.dumps(report, indent=2)}"
                    for specialist, report in self.extra_info.items()
                ])
                prompt = f"""
You are a multidisciplinary medical team synthesizing reports from: {", ".join(self.extra_info.keys())}.

Produce exactly 3 final diagnoses backed by the specialist findings.

Respond ONLY with a valid JSON object — no explanation, no markdown fences:
{{
    "diagnoses": [
        {{"condition": "Name", "reasoning": "backed by which specialists and why"}},
        {{"condition": "Name", "reasoning": "backed by which specialists and why"}},
        {{"condition": "Name", "reasoning": "backed by which specialists and why"}}
    ],
    "overall_urgency": "low|moderate|high|critical",
    "recommended_next_steps": ["step1", "step2", "step3"]
}}

Specialist Reports:
{reports_section}
"""
            else:
                pubmed_context = self.fetch_pubmed_context()
                prompt = AGENT_PROMPTS[self.role].format(
                    medical_report=self.medical_report,
                    pubmed_context=pubmed_context
                )

            response = self.model.invoke(prompt)
            return self.parse_json_response(response.content)

        except Exception as e:
            print(f"Error in {self.role}:", e)
            return None


# ─── Specialist Classes ───────────────────────────────────────────────────────

class Cardiologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Cardiologist")

class Psychologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Psychologist")

class Pulmonologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Pulmonologist")

class Neurologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Neurologist")

class Endocrinologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Endocrinologist")

class Immunologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Immunologist")

class MultidisciplinaryTeam(Agent):
    def __init__(self, specialist_reports: dict):
        super().__init__(role="MultidisciplinaryTeam", extra_info=specialist_reports)