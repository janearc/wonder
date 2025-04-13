# taxonometry

taxonometry is a Wonder concept that measures the difficulty of understanding
concepts within its contextual framework. this is especially useful for
measuring  difficulty presented, linguistically, in understanding assorted 
concepts within the framework. this is necessary because wonder is richly
self-referential and necessarily defines many new concepts. these concepts are
inherently understandable, but require additional processing because they
require an understanding of terms already extant within the framework.

essentially, taxonometry measures the *friction* between the local wonder
context and what wonder calls the orthoreal or orthonormative context. this
data is used to analyze the framework allowing:

- identifying concepts which could be "tuned" for greater legibility
- identifying concepts which may be particularly novel
- identifying concepts which present substantial orthodivergence
- optimizing the software (e.g., python) tooling for optimizing on difficult
  tasks in processing
- assessing whether one model performs better against a different model
- informing the degree to which a trained model has orthodiverged
- correspondingly, because orthodivergence can be measured, alignment can also
  be measured.

# taxonometry heuristic axes

# the data

an example of a taxonometric signature is provided below:

```json
{
  "title": "rupture",
  "zipf_avg": 5.482544378698225,
  "zipf_cluster": [
    7,
    65,
    97
  ],
  "rare_terms": [
    "Metareal",
    "Core sigil",
    "Deeper convergence",
    "Stronger alignment",
    "Erosion of context"
  ],
  "rarity_pos": 0.0196078431372549,
  "benchmark": {
    "label": "lexical_rarity",
    "input_tokens": 339,
    "output_tokens": 31,
    "token_throughput": 4.126588767872757,
    "start_time": 136667.412819958,
    "end_time": 136674.925078083
  }
}
```

## lexical rarity

wonder's taxonometry profiling attempts to use a llm
(meta-llama/Meta-Llama-3-8B-Instruct) to process the sigils defined in the
framework. this process asks the model to identify terms which *"Identify and
extract unusual words or phrases, comprising from one to three words.*" These
words and phrases are then added to a list in the taxonometric signature. the
utility of this function is it allows identifying which words and phrases
appear consistently throughout the corpus which are inherently troublesome to
(orthoconverged) understanding. the aggregate of these throughout the corpus
presents a kind of *legiblity friction surface* that can inform both refining
and expanding meanings, as well as identifying where optimizations or
additional processing may be useful in teaching a model.

## token input, output, throughput

* token input

token input is simply the length of the sigil, tokenized, as measured by
distilgpt2. it is a blunt instrument in assessing complexity, but it allows
measuring of the signal (unique, difficult, lexically rare) within a sigil,
which might be represented as a kind of verbosity vs clarity coefficient.

* token output

for the purposes of these signatures, token output is expressed solely as the
sum of the token length as measured by distilgpt2 of the identified lexically
rare terms and phrases. this is to say, llama 3 is asked to lexically analyze
the text, and then distilgpt2 is used to assess how many tokens are produced
by llama 3. this again could be represented as a verbosity vs clarity
coefficient in concert with token input, but can also be viewed as a sort of
indicator of novelty (although this is not strictly accurate).

* token throughput

token throughput represents, essentially, the performance of the llm in
reducing/assessing the input text (represented as token input) to the
lexically rare phrases and words (represented in token output) divided by
time. so while token output might be seen as a kind of maximally-concise
representation of a concept, token throughput is a representation of how
efficient the model is arriving at that state.

## zipf scores

* zipf average

there are two zipf scores provided. the first, `zipf_avg`, represents the
average zipf score of words in the assessed sigil. this is possibly-meaningful
but because the data tends to be full of not-difficult words and we are more
interested in what is actually difficult to understand, it is probably only
useful in measuring that score over time, vs as a single datapoint of
legibility.

* zipf cluster

in contrast to `zipf_avg`, `zipf_cluster` provides three scores for words
assessed in the sigil. each represents the count of the number of words, with
the first field being those numbers which score 0-3 ("difficult"), second
being 3-5 ("common"), and the last 5+ being those words which are inherently
very easy to understand. this last bucket largely resembles words which can
typically be thrown away when lexically compressing a text to allow it to more
easily fit into the working memory/context window of a language model.

in this way, we can think of sigils with a high count of zipf cluster 3 words as
being good targets for optimization to reduce decoherence/hallucination.

similarly, sigils with a high count of zipf cluster 1 words represent concepts
which would possibly benefit from updates to improve legibility, in keeping
with the ethic of bicameral legibility in wonder. wonder is meant to be a
metaprogramming language, and this is a difficult concept, but it should not
*necessarily* require words which are themselves difficult to understand.

lastly, it may be useful to think of the zipf cluster as a quantification of
the *semantic compression* in a text. going back to the concept of *legiblity
friction surface*, high zipf 0 scores indicate concepts which are highly
lexically compressed through the use of complicated or novel words.
correspondingly, these present legibility friction both for humans and large
language models.

to illustrate these concepts, we can refer to a difficult sigil:

```json
{
  "title": "sigil-tuple",
  "zipf_avg": 5.05214953271028,
  "zipf_cluster": [
    18,
    32,
    57
  ],
  "rare_terms": [
    "Sigil tuple",
    "Interdependence",
    "Pedagogy",
    "Metareal"
  ],
  "rarity_pos": 0.023255813953488372,
  "benchmark": {
    "label": "lexical_rarity",
    "input_tokens": 229,
    "output_tokens": 22,
    "token_throughput": 1.977292073727977,
    "start_time": 136906.800909083,
    "end_time": 136917.927237
  }
}
```

for comparative purposes, this zipf 0 score of this sigil places it in the top
10% of signatures by density.

`sigil-tuple` represents a primitive datatype in wonder which must also
reference another primitive, `sigil`.  furthermore, while `tuple` may be
legible to technical folks reading this document, it is not an especially
commonly used word. thus when we combine the words "sigil" and "tuple" we
create a new phrase which conjoins separate contexts:

- the orthonormative definition of sigil: *an inscribed or painted symbol
  considered to have magical power*
- the metareal, wonder definition of sigil: *a primitive datatype that
  contains a definition which can be referenced elsewhere within wonder*
- data structures and programming: *an ordered, immutable (unchangeable)
  collection of items*

in order to understand this concept, the perceiver must "unpack" or "coalesce"
contextual meaning from different layers of context and arrive at a new
definition that spans all of these contexts while remaining coherent and
legible in this new scope: what wonder calls *metareal.*

as with the other taxonometric signatures provided, the zipf clustering can
reveal concepts which have dense lexical compression through revealing zipf
bucket 0 density.

## pos scores

the `rarity_pos` metric just shows the assessed value from spacy's
part-of-speech analysis. explicitly, this analysis looks for:

- terms which are not otherwise classified (including typos and other
  "strange" and unclassifiable things)
- symbols such as emoji and non-alnum characters
- numbers including both decimal and words like "twenty"
- interjections
- proper nouns (such as Wonder and Cinder)

the number provided is a float which represents the count of the above words
divided by the number of words assessed. put very, very simply, *"higher
`rarity_pos` means less legible."*

# taxonometry tooling

this is something that i'm still working on, but you should be able to run:

```bash
# generate a full taxonometric analysis of the corpus
poetry run python src/wonder_local/modengine.py sigil_profile_all ${WONDER_ROOT}/sigil
```

```bash
# return a list of the sigils which have the highest occurrence of lexically
# rare terms and phrases
find data/taxonometry -name '*.json' \
  -exec jq -r '[.title, (.rare_terms | length)] | @tsv' {} \; | \
  sort -k2 -n
```

```bash
# return a list of sigils sorted by highest number of zipf-difficult words
find data/taxonometry -name '*.json' \
  -exec jq -r '[.title, .zipf_cluster[0]] | @tsv' {} \; | \
  sort -k2 -n
```

```bash
# return a list of sigils sorted by greatest computational time in profiling
find data/taxonometry -name '*.json' \
  -exec jq -r '[.title, (.benchmark.end_time - .benchmark.start_time)] | @tsv' {} \; | \
  sort -k2 -n
```
