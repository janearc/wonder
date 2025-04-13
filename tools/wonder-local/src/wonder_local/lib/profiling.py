import re
from typing import Optional
from pydantic import BaseModel
from wordfreq import zipf_frequency
from wonder_local.lib.markdown_xml import markdown_to_xml
from wonder_local.model.load_model import load_model
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

import spacy

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
    def get_zipf_score(self, text: str, lang: str = "en") -> float:
        # pull our words from the lexed and stripped md->xml
        words = re.findall(r"\b\w+\b", text.lower())

        # sorry, friend, your score is in another castle
        if not words:
            return 0.0

        scores = [zipf_frequency(word, lang, wordlist="large") for word in words]
        return sum(scores) / len(scores)

    def get_pos_rarity(self, text: str) -> float:
        # Estimate lexical rarity based on POS-tag frequency.
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

    def get_llm_rarity(self, model, tokenizer, context: str, input_length: int, logger) -> float:
        rarity_prompt_text = (
            "You are a linguistic researcher evaluating the difficulty of vocabulary in written passages.\n"
            "Consider how technical, symbolic, or uncommon the words are—especially those that wouldn't appear in everyday speech.\n\n"
            "Here is a passage:\n"
            f"\"\"\"\n{context}\n\"\"\"\n\n"
            "Rate the rarity of vocabulary in this passage on a scale from 0.0 to 1.0:\n"
            " - 0.0 = very common, everyday language\n"
            " - 1.0 = highly technical, obscure, symbolic, or rare language\n\n"
            "Give your answer as a float number only. Do not explain."
        )

        inputs = tokenizer(rarity_prompt_text, return_tensors="pt")

        outputs = model.generate(
            **inputs,
            max_length=input_length,
            temperature=0.8,
            top_p=0.95,
            top_k=75,
            do_sample=True,
            num_return_sequences=1,
        )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        logger.info(f"llm rarity output: {result}")

        try:
            return self.normalize_rarity_score(float(result.strip()), method="llm")
        except ValueError:
            logger.warning("Failed to parse LLM rarity response")
            return 0.5

    def normalize_rarity_score(self, value: float, method: str) -> float:
        if method == "pos":
            return max(0.0, min(1.0, value))
        elif method == "llm":
            return max(0.0, min(1.0, value))  # already normalized
        return 0.5  # fallback neutral

    def normalize_zipf(self, zipf: float) -> float:
        # Normalize Zipf range [3.0, 7.0] → [1.0 (simple), 0.0 (rare)]
        clamped = max(3.0, min(7.0, zipf))
        return 1.0 - ((clamped - 3.0) / 4.0)  # invert: low zipf = high rarity

def profile_sigil(self, text: str, title: Optional[str] = None) -> SigilProfile:
    # we assume that we are given markdown, and we convert md to xml
    root = markdown_to_xml(text)
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]
    context = "\n\n".join(paragraphs)

    analyzer = RarityAnalyzer()
    zipf_avg = analyzer.normalize_zipf(analyzer.get_zipf_score(context))
    input_length = self.invoke("estimate", context)

    if input_length < 512:
        # hard call to model, maybe be flexible in the future
        model_name = "google/flan-t5-large"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # so what do you think, flan?
        rarity_llm = analyzer.get_llm_rarity(model, tokenizer, context, input_length, self.logger)
    else:
        self.logger.warning(f"Input length {input_length} exceeds limit (512)")
        rarity_llm = 0.5

    rarity_pos = analyzer.get_pos_rarity(context)

    return SigilProfile(
        title=title or "unknown",
        token_count=input_length,
        zipf_avg=zipf_avg,
        rarity_pos=rarity_pos,
        rarity_llm=rarity_llm,
    )

