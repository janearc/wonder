import re
from typing import Optional
from pydantic import BaseModel
from wordfreq import zipf_frequency
from wonder_local.lib.markdown_xml import markdown_to_xml

import spacy
from llama_cpp import Llama

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
    rarity_pos: float  # 0-1 normalized rarity via POS tags
    rarity_llm: float  # 0-1 normalized rarity via LLM

class RarityAnalyzer:
    def __init__(self):
        default_gguf="/Users/jane/.cache/huggingface/hub/models--mradermacher--KONI-Llama3.1-8B-Instruct-20241024-i1-GGUF/snapshots/71f2e2fb2c081e980b9e92e750ff2eee23677bda/KONI-Llama3.1-8B-Instruct-20241024.i1-Q6_K.gguf"
        self.model = Llama(model_path=default_gguf)

    def get_zipf_score(self, text: str, lang: str = "en") -> float:
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0
        scores = [zipf_frequency(word, lang, wordlist="large") for word in words]
        return sum(scores) / len(scores)

    def get_pos_rarity(self, text: str) -> float:
        if not nlp:
            return 0.5
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
            "You are a language model evaluator. You will receive a passage of English text. "
            "Your task is to assess how lexically rare the vocabulary is, returning a float from 0.0 (extremely common) to 1.0 (extremely rare). "
            "Respond only with a single float. Do not explain. Do not add any commentary. Example: 0.42\n\n"
            f"Passage:\n{context}\n\n"
            "Return only the float on the next line.\nScore:\n"
        )

        try:
            response = self.model(
                prompt=prompt,
                max_tokens=16,
                temperature=0.8,
                top_k=750,
                top_p=0.90,
                stop=["\n", "<|eot_id|>", "<|end_of_text|>"],
            )

            logger.info(f"🔍 Full LLM response: {response}")
            result = response["choices"][0]["text"].strip()
            logger.info(f"llm rarity output: {result}")
    
            match = re.search(r"(\d\.\d+)", result)
            if not match:
                # Try line-by-line in case it's not the first token
                for line in result.splitlines():
                    match = re.search(r"(\d\.\d+)", line)
                    if match:
                        return self.normalize_rarity_score(float(match.group()), method="llm")
            else:
                logger.warning("LLM output contained no float value")
                return 0.5

        except Exception as e:
            logger.warning(f"Failed to generate or parse LLM rarity: {e}")
            return 0.5

        return self.normalize_rarity_score(float(result), method="llm")


    def normalize_rarity_score(self, value: float, method: str) -> float:
        if method == "pos":
            return max(0.0, min(1.0, value))
        elif method == "llm":
            return max(0.0, min(1.0, value))
        return 0.5

def profile_sigil(self, text: str, title: Optional[str] = None) -> SigilProfile:
    # we assume that we are given markdown, and we convert md to xml
    root = markdown_to_xml(text)
    # then we pull the text out of the xml rather than regexing
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]
    # then we join on newlines for the model
    context = "\n\n".join(paragraphs)

    analyzer = RarityAnalyzer()
    zipf_avg = analyzer.get_zipf_score(context)
    input_length = self.invoke("estimate", context)

    rarity_llm = analyzer.get_llm_rarity(context, self.logger)
    rarity_pos = analyzer.get_pos_rarity(context)

    return SigilProfile(
        title=title or "unknown",
        token_count=input_length,
        zipf_avg=zipf_avg,
        rarity_pos=rarity_pos,
        rarity_llm=rarity_llm,
    )

