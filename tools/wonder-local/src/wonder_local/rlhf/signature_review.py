from pathlib import Path
from wonder_local.lib.profiling import (
    SigilProfileCorpus,
    DataToSigilProfileCorpus,
)

def load_signatures(self, *args):
    self.logger.info(f"arguments: {args}")
    data_dir = args[0]
    self.logger.info(f"reading {data_dir} to find signature data")

    spc = DataToSigilProfileCorpus(data=data_dir)
    count = spc.length
    self.logger.info(f"discovered {count} signatures")

def report_missing_rarity(self, *args):
    self.logger.info(f"arguments: {args}")
    data_dir = args[0]
    self.logger.info(f"reading {data_dir} to find signature data")

    spc = DataToSigilProfileCorpus(data=data_dir)
    missing_rares = spc.no_rare_terms()

    # this is just a list, not a corpus
    count = len(missing_rares)
    self.logger.info(f"discovered {count} malformed signatures")

    # extract the filenames of the signatures without rare terms
    missing_rarity_files = spc.no_rare_term_filenames()

    for filename in missing_rarity_files:
        self.logger.info(f"malformed signature: {filename}") 
