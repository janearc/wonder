import re
from typing import Optional, List
from pydantic import BaseModel
from wordfreq import zipf_frequency
from wonder_local.lib.markdown_xml import markdown_to_xml
import spacy
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Try to load spaCy, fallback logic can go here if needed
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    nlp = None
    print(f"⚠️ spaCy failed to load: {e}")

class SigilProfile(BaseModel):
    title: str
    token_count: int
    zipf_avg: float
    rare_terms: int
    rarity_pos: float  # 0-1 normalized rarity via POS tags
    rarity_llm: float  # 0-1 normalized rarity via LLM

class RarityAnalyzer:
    def __init__(self):
        model_path = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")
        self.model.eval()

    def get_zipf_score(self, text: str, lang: str = "en") -> float:
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0
        scores = [zipf_frequency(word, lang, wordlist="large") for word in words]
        return sum(scores) / len(scores)

    def get_pos_rarity(self, text: str) -> float:
        if not nlp:
            return 0.5  # fallback neutral score
        doc = nlp(text)
        rare_tags = {"X", "SYM", "NUM", "INTJ", "PROPN"}
        rare_count = sum(1 for token in doc if token.pos_ in rare_tags)
        total = len(doc)
        if total == 0:
            return 0.5
        ratio = rare_count / total
        return self.normalize_rarity_score(ratio, method="pos")

    def get_llm_rarity(self, context: str, logger) -> float:
        prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
            "You are a linguistic analysis expert. Given a passage, you will rate its lexical rarity."
            " Just return a float from 0.0 (very common) to 1.0 (very rare)."
            " Respond with only the floating point number, no explanation."
            f"Rate the lexical rarity of the following passage: {context} \n\n"
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=256, temperature=0.7, top_k=750, top_p=0.90)
        result = self.tokenizer.decode(output[0], skip_special_tokens=True)

        logger.info(f"🔍 Full LLM response: {result}")
        try:
            match = re.search(r"\d+\.\d+", result)
            if match:
                return self.normalize_rarity_score(float(match.group()), method="llm")
            else:
                logger.warning("LLM output contained no float value")
                return 0.5
        except Exception as e:
            logger.warning(f"Failed to generate or parse LLM rarity: {e}")
            return 0.5

    def extract_rare_terms(self, context: str, logger) -> List[str]:
        prompt = (
            "Given the passage below, starting with <|PASSAGE|> and ending with <|END|>. "
            "Below is a passage. Identify and extract unusual words or phrases, comprising from one to three words. "
            "Respond with a list of these terms, each starting with the marker ##.\n\n"
            f"<|PASSAGE|>\n\n{context}\n\n<|END|>"
        )
    
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=128, temperature=0.7, top_k=750, top_p=0.95)
    
        result = self.tokenizer.decode(output[0], skip_special_tokens=True)
        logger.debug(f"🔍 Full LLM response: {result}")
    
        terms = []
        for line in result.splitlines():
            match = re.search(r"##\s*(.+)", line)
            if match:
                term = match.group(1).strip()
                if term and term[-1].isalpha():
                    terms.append(term)
    
        logger.debug(f"✅ Cleaned rare terms: {terms}")
        return terms

    def normalize_rarity_score(self, value: float, method: str) -> float:
        if method == "pos":
            return max(0.0, min(1.0, value))
        elif method == "llm":
            return max(0.0, min(1.0, value))
        return 0.5

def profile_sigil(self, text: str, title: Optional[str] = None, estimate_tokens=None, logger=None) -> SigilProfile:
    root = markdown_to_xml(text)
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]
    context = "\n\n".join(paragraphs)

    analyzer = RarityAnalyzer()
    zipf_avg = analyzer.get_zipf_score(context)
    token_count = estimate_tokens(context) if estimate_tokens else len(context.split())
    rare_terms = analyzer.extract_rare_terms(context, self.logger)
    rarity_pos = analyzer.get_pos_rarity(context)

    return SigilProfile(
        title=title or "unknown",
        token_count=token_count,
        zipf_avg=zipf_avg,
        rarity_pos=rarity_pos,
        rare_terms=len(rare_terms),
        rarity_llm=0.5
    )

