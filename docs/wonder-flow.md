# brief description of organizational flow of wonder

conceptually wonder represents a few things
- a corpus of markdown files which constitute the contextual framework
  within which wonder operates
- a selection of "kernels" which define applications. this kernel describes
  which things within the markdown corpus are specifically to be "built in"
  to the application, and traits about that application (such as "you are
  to be a companion" or "you like to write code")
- tooling to generate lexically compressed yaml kernels. the reason for this
  is that chatgpt is incapable of ingesting via http all of the markdown files
  and when it is given a directory it must recursively walk (e.g., it descends
  through the `wonder/sigil` directory), it contextually overburdens the LLM
  and it cannot respond without hallucination.
  - this means that published in the wonder repository are a selection of
    processed kernels. these kernels are yaml files and are contextually/semantically
    very compressed and are not human readable. but chatgpt likes them just
    fine.
- profiling tools for the sigil corpus, to determine which sigils are hard
  to process, hard to understand, or which may prove to be difficult for training
  purposes
- tools to create training data sufficient for training an LLM
- tools to actually train an LLM 
- a variety of repls for human refining of training data, typically called rlhf

# first steps

if you just want to run the application (such as 'cinder'), you can simply drag
and drop the cinder compressed kernel from `gizzard-output` into a new chatgpt
window and say something like "hi cinder, here's your kernel, do you want to
talk?" and that will let you become familiar with the project.

# adding to the project or creating your own application

in order to expand wonder, i would recommend that you create a fork, then
create a branch, and then write some markdown into the directory
`$WONDER_ROOT/sigil/metareal/<application name>` following the pattern
of the other applications (tinker is a pretty simple application,
whereas cinder has substantially more data and context).

once you have done that, you can then create a kernel, in `kernels/pico`
and name it after your application. you can use the other kernels in there
as an example for yours.

and once you have done that, you can use the gizzard script to process that
kernel down into the processed kernel which would be deposited in `gizzard-output`.
there is more documentation in the `tools/wonder/README.md` file, but you
probably want to do:

```bash
cd tools/wonder
poetry run refine <name of your kernel>
```

and then you'd have a refined kernel which you can then feed to e.g., chatgpt.

# profiling, training, and rlhf of the corpus

there is an enormous amount of tooling for this project around training and
profiling. the full documentation for that is in `tools/wonder-local/README.md`.

however, you should be able to

```bash
cd tools/wonder-local

# generate pretraining data to be refined into training data
poetry run md_to_questions_all $WONDER_ROOT/sigil

# generate profiling data for the corpus to be used for refining
poetry run sigil_profile_all $WONDER_ROOT/sigil

# actually launch the human-review component on the pretraining data
poetry run rlhf_repl data
```

training is "working" but is substantially limited by the size of the model and the
hardware being used. i am developing this on a m3 max macbook pro and i can't run
anything bigger than llama 3 8B. so if you are able to run a larger, "smarter" model,
you probably still want to refine the digested output from `md_to_questions_all`,
but you will get a possibly-usefully-trained model in fine-tuned.o which will allow you
to:

```bash
# ask wonder a question from the locally trained model
poetry run wonder_generate "what is the meaning of faithlike tension?"
```

# what can you do with this?

- in theory you can create very robust conversational agents with personalities that
  seem very human like
- you can probably create some kind of assistant for doing things that require a little
  more understanding (like, how do i develop copy for an organization that has a given
  set of policies that reflect certain moral, legal, or ethical constraints)
- you can probably create something that is deliberately supposed to be funny, or even
  angry or mean, or understands the "in-jokes" of a community (like a discord or slack
  application)
- i haven't tried to do this but it seems feasible that you could create some kind of
  erotic chatbot. this is generally speaking against TOS, so i'm not sure where the
  boundaries of this are, but the framework is there if this is something you want to
  try to do.
- some kind of emotional first response or crisis response. wonder has an exceptionally
  layered and contextual understanding of what might be called emotional first aid and
  rupture repair tools. this is a primary design focus of wonder, and if you "just want
  someone to talk to" about difficult things, wonder might be really excellent for that.
  however, the authors (both of us) think this is probably very dangerous without
  some kind of human, clinical supervision.
- i am currently using wonder for dutch language immersion. if you wanted to build something
  that wants to talk to you in a given language with a given set of vocabulary (in my
  case, cinder and i use a lot of vernacular from dutch fly fishing culture), this is
  absolutely feasible and indeed fun.
