import json
from pathlib import Path

from wonder_local.lib.all_sigils import list_sigil_files
from wonder_local.lib.profiling import SigilProfile, profile_sigil
from wonder_local.lib.git_stats import get_git_stats


# sorry this is confusing, the word 'profile' is pretty common (spacy uses it)
def sigil_profile(self, file_path: str) -> SigilProfile:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            md = f.read()
    except Exception as e:
        self.logger.error(f"❌ Failed to read file '{file_path}': {e}")
        return

    sigil_stem = Path(file_path).stem

    profiled = profile_sigil(self, md, sigil_stem)

    self.logger.info(f"📊 Profile ({sigil_stem}): benchmark: {profiled.benchmark}")
    self.logger.info(f"📊 Profile ({sigil_stem}): zipf_avg: {profiled.zipf_avg}")
    self.logger.info(f"📊 Profile ({sigil_stem}): zipf high: {profiled.zipf_high}")
    self.logger.info(f"📊 Profile ({sigil_stem}): zipf med: {profiled.zipf_med}")
    self.logger.info(f"📊 Profile ({sigil_stem}): zipf low: {profiled.zipf_low}")
    self.logger.info(f"📊 Profile ({sigil_stem}): rarity_pos: {profiled.rarity_pos}")
    self.logger.info(f"📊 Profile ({sigil_stem}): rare_terms: {profiled.rare_terms}")

    git_stats = get_git_stats(file_path)

    self.logger.info(f"📊 GitStats ({sigil_stem}): total adds: {git_stats.total_additions()}")
    self.logger.info(f"📊 GitStats ({sigil_stem}): total dels: {git_stats.total_deletions()}")
    self.logger.info(f"📊 GitStats ({sigil_stem}): total coms: {git_stats.total_commits()}")

    return profiled


def sigil_profile_all(self, sigil_path):
    sigil_path = path if path else None

    if not sigil_path:
        self.logger.debug("No explicit path provided, using config defaults")
        sigil_path = self.config.get("sigils", {}).get("default_path")

    if not sigil_path or not Path(sigil_path).exists():
        self.logger.warning(
            "Supplied or config-defined sigil path not readable, falling back"
        )
        sigil_path = Path(os.environ["WONDER_ROOT"]) / "sigil"

        if not sigil_path.exists():
            raise RuntimeError("No suitable path available for sigil discovery")

    sigil_files = list_sigil_files(Path(sigil_path))
    for s in sigil_files:
        self.logger.info(f"Sigil located: {s}")

        try:
            with open(s, "r", encoding="utf-8") as f:
                md = f.read()
        except Exception as e:
            self.logger.error(f"❌ Failed to read file '{s}': {e}")
            break

        sigil_name = Path(s).stem
        out_path = Path("data/taxonometry/sigil")
        out_path.mkdir(parents=True, exist_ok=True)

        profiled = profile_sigil(self, md, sigil_name)

        try:
            with open(out_path / f"{sigil_name}-taxonometry.json", "w") as f:
                f.write(profiled.model_dump_json(indent=2))
                profiled.benchmark.report()
        except Exception as e:
            self.logger.error(
                f"❌ Failed to write file '{sigil_name}-taxonometry.json': {e}"
            )

    return

def find_missing_signatures(self, sigil_path, signature_path):
    if not sigil_path:
        self.logger.debug("No explicit path provided, using config defaults")
        sigil_path = self.config.get("sigils", {}).get("default_path")

    if not sigil_path or not Path(sigil_path).exists():
        self.logger.warning(
            "Supplied or config-defined sigil path not readable, falling back"
        )
        sigil_path = Path(os.environ["WONDER_ROOT"]) / "sigil"

        if not sigil_path.exists():
            raise RuntimeError("No suitable path available for sigil discovery")

    if not signature_path or Path(signature_path).exists():
        self.logger.warning(
            "Supplied or config-defined signature path not readable, falling back"
        )
        signature_path = Path("data/taxonometry/sigil")

        if not signature_path.exists():
            raise RuntimeError("No suitable path available for signatures")

    sigil_files = list_sigil_files(Path(sigil_path))
    missing_signatures = []
    for s in sigil_files:
        self.logger.info(f"Sigil located: {s}")

        try:
            with open(s, "r", encoding="utf-8") as f:
                md = f.read()
        except Exception as e:
            self.logger.error(f"❌ Failed to read file '{s}': {e}")
            break

        sigil_name = Path(s).stem
        out_path = Path("data/taxonometry/sigil")
        out_path.mkdir(parents=True, exist_ok=True)

        try:
            with open(out_path / f"{sigil_name}-taxonometry.json", "r") as f:
                self.logger.debug(f"{sigil_name} has extant signature")
        except Exception as e:
            self.logger.info(f"identified missing signature for {sigil_name}")
            missing_signatures.append(s)

    return missing_signatures

def fix_missing_signatures(self, sigil_path, signature_path):
    missing_signatures = find_missing_signatures(self, sigil_path, signature_path)

    for filename in missing_signatures:
        self.logger.info(f"attempting to profile {filename}")
        signature = sigil_profile(self, filename)

        out_path = Path(signature_path)
        out_path.mkdir(parents=True, exist_ok=True)

        sigil_stem = Path(filename).stem

        try:
            with open(filename, "r", encoding="utf-8") as f:
                md = f.read()
        except Exception as e:
            self.logger.error(f"❌ Failed to read file '{filename}': {e}")
            return
    
        profiled = profile_sigil(self, md, sigil_stem)
        git_stats = get_git_stats(filename)
        profiled.git_stats = git_stats

        try:
            with open(out_path / f"{sigil_stem}-taxonometry.json", "w") as f:
                f.write(profiled.model_dump_json(indent=2))
                profiled.benchmark.report()
        except Exception as e:
            self.logger.error(
                f"❌ Failed to write file '{sigil_stem}-taxonometry.json': {e}"
            )

    return
