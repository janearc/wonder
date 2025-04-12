import re
from typing import Optional
from pydantic import BaseModel
from wordfreq import zipf_frequency
from wonder_local.lib.markdown_xml import markdown_to_xml
from wonder_local.model.load_model import load_model

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
    def get_zipf_score(text: str, lang: str = "en") -> float:
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

    def get_llm_rarity(self, model, tokenizer, context: str, ) -> float:
        rarity_prompt_text = (
            "You are an expert linguist analyzing the vocabulary difficulty of a passage."
            "Rate the rarity of the vocabulary on a scale from 0.0 to 1.0."
            "0.0 = Very common, everyday language"
            "1.0 = Highly technical, obscure, symbolic, or rare vocabulary"
            "Just reply with a float number between 0.0 and 1.0. Do not include any explanation.\n\n"
            
            "Text:\n\n {context}"
        )

        inputs = tokenizer(question_prompt, return_tensors"pt")

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

        self.logger.info(f"llm rarity output: {result}")

        return self.normalize_rarity_score(result, method="llm")

    def normalize_rarity_score(self, value: float, method: str) -> float:
        if method == "pos":
            # already a ratio, just clamp
            return max(0.0, min(1.0, value))
        elif method == "llm":
            # expected range is 1-10, normalize to 0-1
            return max(0.0, min(1.0, (value - 1) / 9))
        return 0.5  # fallback neutral


def profile_sigil(text: str, title: Optional[str] = None) -> SigilProfile:
    # we assume that we are given markdown, and we convert md to xml
    root = markdown_to_xml(text)
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]
    context = "\n\n".join(paragraphs)

    zipf_avg = get_zipf_score(context)

    analyzer = RarityAnalyzer()

    # Estimate input token length
    input_length = self.invoke("estimate", context)

    if input_length < 512:
        # Grab flan for estimation purposes
        model, tokenizer, device = self.invoke("load_model", "google/flan-t5-large")
    
        if model:
            rarity_llm = analyzer.get_llm_rarity(context, model)
        else:
            self.logger.warning("Failed to load model (flan)")
            rarity_llm = 0.5
     else:
        self.logger.warning(f"Input length {input_length} exceeds limit (512)")

    rarity_pos = analyzer.get_pos_rarity(context)

    return SigilProfile(
        title=title or "unknown",
        token_count=input_length,
        zipf_avg=zipf_avg,
        rarity_pos=rarity_pos,
        rarity_llm=rarity_llm,
    )
