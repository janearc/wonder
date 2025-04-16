from pathlib import Path
from datetime import datetime
import re
import json
from functools import lru_cache
from typing import List, Optional

import spacy
import torch
from pydantic import BaseModel, Field, ConfigDict
from transformers import AutoModelForCausalLM, AutoTokenizer
from wonder_local.lib.benchmark import Benchmark
from wonder_local.lib.markdown_xml import markdown_to_xml
from wordfreq import zipf_frequency
from wonder_local.lib.git_stats import GitStats

# Try to load spaCy, fallback logic can go here if needed
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    nlp = None
    print(f"⚠️ spaCy failed to load: {e}")


@lru_cache(maxsize=1)
def get_tokenizer_and_model():
    # TODO: i'm not sure we can change this given the specificity of our prompts below
    #       but i very much would prefer to
    model_path = "meta-llama/Meta-Llama-3-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16, device_map="auto"
    )
    model.eval()
    return tokenizer, model

class SigilProfile(BaseModel):
    title: str
    zipf_avg: float
    zipf_cluster: List[int]
    rare_terms: List[str]
    rarity_pos: float  # 0-1 normalized rarity via POS tags

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    # our native benchmarking class to include in the profile
    benchmark: Optional[Benchmark]

    # indicate the filename for later review
    filename: Optional[str] = Field(
        None, description="The source filename of the signature (for tracking)."
    )

    # add the git stats if available
    git_stats: Optional[GitStats] = Field(
        None, description="git statistics for the sigil being profiled."
    )

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

class SigilProfileCorpus(BaseModel):
    signatures: List[SigilProfile] = Field(
        ..., description="a full set of sigil taxonometric signatures"
    )

    # Number of signatures loaded
    @property
    def length(self) -> int:
        return len(self.signatures)

    # Removes and returns the first SigilProfile
    def pop(self) -> SigilProfile:
        return self.signatures.pop(0)

    # Adds a SigilProfile to the end
    def push(self, qset: SigilProfile):
        self.sets.append(qset)

    # Returns all SigilProfiles with no rare terms
    def no_rare_terms(self) -> List[SigilProfile]:
        return [sig for sig in self.signatures if sig.rare_term_count == 0]

    # Returns filenames of all SigilProfiles with no rare terms
    def no_rare_term_filenames(self) -> List[str]:
        return [
            sig.filename for sig in self.signatures
            if sig.rare_term_count == 0 and sig.filename is not None
        ]


class RarityAnalyzer:
    def __init__(self, token_count: int, modengine):
        # instantiate our benchmark object
        benchmark = Benchmark(label="lexical_rarity", input_tokens=token_count)
        benchmark.start()
        self.benchmark = benchmark

        self.tokenizer, self.model = get_tokenizer_and_model()
        self.modengine = modengine

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

    # assess part-of-speech (pos) rarity score using spacy
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

        # this is hard to compare to the other metrics, but lower numbers are less difficult
        # to read/understand and higher numbers are more difficult.
        return ratio

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
            output = self.model.generate(
                **inputs, max_new_tokens=128, temperature=0.7, top_k=750, top_p=0.95
            )

        result = self.tokenizer.decode(output[0], skip_special_tokens=True)
        logger.debug(f"🔍 Full LLM response: {result}")

        # the model can get kind of sassy so we need to really be careful looking through the output
        # for stuff that looks correct
        terms = []
        seen = set()
        for line in result.splitlines():
            match = re.search(r"##\s*(.+)", line)
            if match:
                term = match.group(1).strip()
                if term and term[-1].isalpha() and term not in seen:
                    seen.add(term)
                    terms.append(term)

        logger.debug(f"✅ Cleaned rare terms: {terms}")

        joined = ", ".join(terms)

        self.benchmark.output_tokens = self.modengine.invoke("estimate", joined)

        return terms


def profile_sigil(
    self, text: str, title: Optional[str] = None, estimate_tokens=None, logger=None
) -> SigilProfile:
    # this slurps in markdown, converts to xml, then uses xml parsing to flatten everything
    root = markdown_to_xml(text)

    # pull out the text from the flattened xml
    paragraphs = [elem.text for elem in root.findall("p") if elem.text]

    # create a wad of text for our analysis methods
    context = "\n\n".join(paragraphs)

    # Dynamically estimate the ideal max length for the response
    token_count = self.invoke("estimate", context)

    # instantiate analyzer
    analyzer = RarityAnalyzer(token_count, self)

    # zipf analysis
    zipf_avg = analyzer.get_zipf_score(context)
    zipf_cluster = analyzer.get_zipf_cluster(context)

    # pos analysis
    rarity_pos = analyzer.get_pos_rarity(context)

    # llm-based analysis
    rare_terms = analyzer.extract_rare_terms(context, self.logger)

    # stop the benchmark
    analyzer.benchmark.stop()

    return SigilProfile(
        title=title or "unknown",
        zipf_avg=zipf_avg,
        zipf_cluster=zipf_cluster,
        rarity_pos=rarity_pos,
        rare_terms=rare_terms,
        benchmark=analyzer.benchmark,
    )

def DataToSigilProfileCorpus(data: str) -> SigilProfileCorpus:
    root = Path(data)
    files = root.glob("**/*-taxonometry.json")
    signatures = []

    for file in files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
                signature = SigilProfile(**data)
                signature.filename = str(file)
                signatures.append(signature)
        except Exception as e:
            raise RuntimeError(f"Failed to load {file}: {e}")

    return SigilProfileCorpus(signatures=signatures)
