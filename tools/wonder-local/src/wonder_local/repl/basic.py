from wonder_local.lib.modengine import ModularInferenceEngine
from wonder_local.lib.repl import InteractiveShell


# Just a toy interpreter for now
def repl(self, *args):
    shell = InteractiveShell(
        name="basic",
        prompt_str="next > ",
        heap=["Hello world", "This is Wonder", "Enjoy the ride"],
        modengine=self,
    )
    shell.run()
