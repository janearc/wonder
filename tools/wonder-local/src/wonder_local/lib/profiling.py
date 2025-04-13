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
    zipf_cluster: List[int]
    rare_terms: List[str]
    rarity_pos: float  # 0-1 normalized rarity via POS tags

    # llm derived "rare or unusual words" count
    @property
    def rare_term_count(self) -> int:
        return len(self.rare_terms)

    # zipf buckets (count, not list):

    # zipf uncommon/difficult words
    @property
    def zipf_high(self) -> int:
        return self.zipf_cluster[0]

    # zipf medium words
    @property
    def zipf_med(self) -> int:
        return self.zipf_cluster[1]

    # zipf common words
    @property
    def zipf_low(self) -> int:
        return self.zipf_cluster[2]

class RarityAnalyzer:
    def __init__(self):
        # TODO: i'm not sure we can change this given the specificity of our prompts below
        #       but i very much would prefer to
        model_path = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")
        self.model.eval()

    # get the average zipf score of the text
    def get_zipf_score(self, text: str, lang: str = "en") -> float:
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0
        scores = [zipf_frequency(word, lang, wordlist="large") for word in words]
        return sum(scores) / len(scores)

    # get a bucket distribution of zipf scores
    def get_zipf_cluster(self, text: str, lang: str = "en") -> List[int]:
        cluster = [0, 0, 0]  # [0–3] high, [3–5] medium, [5+] low
        words = re.findall(r"\b\w+\b", text.lower())
        for word in words:
            score = zipf_frequency(word, lang, wordlist="large")
            if score < 3:
                cluster[0] += 1
            elif score < 5:
                cluster[1] += 1
            else:
                cluster[2] += 1
        return cluster

    # assess part-of-speech (pos) rarity score using stacy
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
        return max(0.0, min(1.0, ratio))

    def extract_rare_terms(self, context: str, logger) -> List[str]:
        prompt = (
            "Given the passage below, starting with <|PASSAGE|> and ending with <|END|>. "
            "Below is a passage. Identify and extract unusual words or phrases, comprising from one to three words. "
            "Respond with a list of these terms, each starting with the marker ##.\n\n"
            f"<|PASSAGE|>\n\n{context}\n\n<|END|>"
        )
    
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            # this top_k is very spicy and could probably be turned down but was working well, so we keep it
            output = self.model.generate(**inputs, max_new_tokens=128, temperature=0.7, top_k=750, top_p=0.95)
    
        result = self.tokenizer.decode(output[0], skip_special_tokens=True)
        logger.debug(f"🔍 Full LLM response: {result}")
    
        # the model can get kind of sassy so we need to really be careful looking through the output
        # for stuff that looks correct
        terms = []
        for line in result.splitlines():
            match = re.search(r"##\s*(.+)", line)
            if match:
                term = match.group(1).strip()
                if term and term[-1].isalpha():
                    terms.append(term)
    
        logger.debug(f"✅ Cleaned rare terms: {terms}")
        return terms

def profile_sigil(self, text: str, title: Optional[str] = None, estimate_tokens=None, logger=None) -> SigilProfile:
    # this slurps in markdown, converts to xml, then uses xml parsing to flatten everything
    root = markdown_to_xml(text)

    # pull out the text from the flattened xml
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]

    # Dynamically estimate the ideal max length for the response
    token_count = self.invoke("estimate", context)

    # create a wad of text for our analysis methods
    context = "\n\n".join(paragraphs)

    # instantiate analyzer
    analyzer = RarityAnalyzer()

    # zipf analysis
    zipf_avg = analyzer.get_zipf_score(context)
    zipf_cluster = analyzer.get_zipf_cluster(context)

    # pos analysis
    rarity_pos = analyzer.get_pos_rarity(context)

    # llm-based analysis
    rare_terms = analyzer.extract_rare_terms(context, self.logger)

    return SigilProfile(
        title=title or "unknown",
        token_count=token_count,
        zipf_avg=zipf_avg,
        zipf_cluster=zipf_cluster
        rarity_pos=rarity_pos,
        rare_terms=rare_terms,
    )

