import json
from pathlib import Path
from wonder_local.lib.profiling import profile_sigil, SigilProfile
from wonder_local.lib.all_sigils import list_sigil_files

# sorry this is confusing, the word 'profile' is pretty common (stacy uses it)
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

    return profiled

def sigil_profile_all(self, path):
    sigil_path = path if path else None

    if not sigil_path:
        self.logger.debug("No explicit path provided, using config defaults")
        sigil_path = self.config.get("sigils", {}).get("default_path")

    if not sigil_path or not Path(sigil_path).exists():
        self.logger.warning("Supplied or config-defined sigil path not readable, falling back")
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
                json.dump(profiled.model_dump(), f, indent=2)
                profiled.benchmark.report()
        except Exception as e:
            self.logger.error(f"❌ Failed to write file '{sigil_name}-taxonometry.json': {e}")

    return
