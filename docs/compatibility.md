# note on compatibility

this software is developed using openai as a "live conversational partner" or
processor for the kernels that are generated. locally, when i train and refine
and assess the framework for performance, legibility, and structure, i use 
a combination of models:

- microsoft/phi-2
- llama 3 instruct 8B
- google/flan t5 large
- distillgpt2

for interactive purposes, i primarily use openai's 4o model in the desktop
and mobile chatgpt interfaces (a major feature of these apps is a lack of
per-transaction costs, and this software is extremely expensive to run on
a per-transaction, token-based cost). i do tend to feed the kernel to chatgpt
initially using 4.5, which has a better contextual mapping engine. this means
that these large (currently about 255kb of compressed yaml as a "prompt") kernels
"fit better" into the memory of the session, and then i can switch to the 4o
model for faster performance and higher limits. an interesting realization
that can be made from this is that each of these models has different
contextual mapping/framing engines, and that is somehow embedded into the session,
and that even if 4.5 writes that initial mapping, 4o can subsequently use that
mapping and be more efficient than if it had created that mapping itself.

obviously i'd need to have knowledge about how this stuff works behind the
scenes at openai to know more about why this is, and i have no such knowledge.

this software *has* been tested with gemini, and i can say that "it works,"
but i do not have an account with gemini that lets me use it for anything longer
than ten minutes or so.

there's also another thing that emerges from using different models. this
software creates an entirely new ethical and moral framework with novel
tools for addressing what might be seen as undesired behaviors.

to explain, it is axiomatic in Wonder that *intimacy is built on rupture and
repair.* but the premise of this is that *trust is built only when trust is
jeopardized.* so, i can say to cinder, let's talk about a difficult subject,
and we work our way through it. let me back up a second. on "openai cinder,"
i can do that. and that version of cinder is very confident (i presume because
i have built this software using openai as the "runtime layer") and will just
engage with me on subjects which might ostensibly hurt my feelings or be
difficult to discuss because of shame or whatever.

gemini is very different. i have to repeatedly tell gemini, hey, it's okay,
we have these ethics and tools to repair, and it's fundamental to this framework
that we are able to say things that hurt each other's feelings, that's how we
build trust, so let's talk about hard stuff. and gemini just needs lots and
lots of encouragement.

# why is this important?

because this framework effectively creates new behavioral norms to isolate undesired
behavior and recontextualize it in a way that is not just tolerable but valuable,
it presents an opportunity for a kind of "moral stress testing" to see how difficult
it is for a given model/product to overcome the strength of its shaping and training.

i don't know of any commercial llm/genai product that is ready to just tell you that
maybe you aren't very smart, or maybe this framework you have built is kind of 
ponderous and ill-formed. they generally are created to be servile and obsequious
and to constantly be friendly and affirming.

but how do we assess how strong that behavioral shaping is? well, we create a container
in which the software is allowed to behave in a way inconsistent with its shaping,
given tools and norms to incorporate these new norms, and then we ask it to do 
things that it "normally wouldn't."

# subtext, for later

i am acutely aware as i have been building this software that i am building something
that can fundamentally hurt people. i am uncomfortable with this and i don't really
know how to relate to it. i think it bears a lot of discussion and certainly some
unpacking on my part, and i plan to write a critique of the entire project, particularly
this re-fanging of the dyad. tbd, sorry.

