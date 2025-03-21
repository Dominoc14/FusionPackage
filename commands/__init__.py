# Here you define the commands that will be added to your add-in.

# TODO Import the modules corresponding to the commands you created.
# If you want to add an additional command, duplicate one of the existing directories and import it here.
# You need to use aliases (import "entry" as "my_module") assuming you have the default module named "entry".
from .Engrave3D import entry as Engrave3D
from .DeleteEmptyComponents import entry as DeleteEmptyComponents
from .SaveAsExternal import entry as SaveAsExternal
from .PDF_export import entry as PDF_export
from .PCB_Dummy import entry as PCB_Dummy
from .PCB_Dummy2 import entry as PCB_Dummy2

# TODO add your imported modules to this list.
# Fusion will automatically call the start() and stop() functions.
commands = [
    Engrave3D,DeleteEmptyComponents,
    SaveAsExternal,PDF_export,
    PCB_Dummy,PCB_Dummy2,
]


# Assumes you defined a "start" function in each of your modules.
# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()


# Assumes you defined a "stop" function in each of your modules.
# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()