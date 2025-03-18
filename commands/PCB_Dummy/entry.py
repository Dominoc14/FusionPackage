import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# Command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_PCB_Dummy'
CMD_NAME = 'PCB To Dummy'
CMD_Description = 'Create a box with the over all dimention of the original PCB'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Location of the command
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tab_id
TAB_NAME = config.tab_name
PANEL_ID = config.clean_CAD_panl_id
PANEL_NAME = config.clean_CAD_panl_name
PANEL_AFTER = ''


# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # ******************************** Create Command Definition ********************************
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******************************** Create Command Control ********************************
    # Get target workspace for the command.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get target toolbar tab for the command and create the tab if necessary.
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    # Get target panel for the command and and create the panel if necessary.
    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, PANEL_AFTER, False)

    # Create the command control, i.e. a button in the UI.
    control = panel.controls.addCommand(cmd_def)

    # Now you can set various options on the control such as promoting it to always be shown.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function to be called when a user clicks the corresponding button in the UI.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    inputs = args.command.commandInputs

    # Create the title of the UI box
    title_box = inputs.addTextBoxCommandInput('title_box', '', 'PCB Selection', 1, True)

    # Create a selection input, apply filters and set the selection limits
    selection_input = inputs.addSelectionInput('selection_input', 'Occurrence Selection', 'Select Occurence')
    selection_input.addSelectionFilter('Occurrences')
    selection_input.setSelectionLimits(1, 1)

    # Create some text boxes for the part number
    title_box.isFullWidth = True
    Name_input =  inputs.addTextBoxCommandInput('text_box', "Dummy's name", 'dummy', 1, False)




# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    selection_input : adsk.core.SelectionCommandInput = inputs.itemById('selection_input')
    text_box: adsk.core.TextBoxCommandInput = inputs.itemById('text_box')

    # Définie Text pour être le nom du dummy
    text = text_box.text

    selection = selection_input.selection(0)
    selected_entity = selection.entity
    # Sketch
    design = app.activeProduct
    rootComp = design.rootComponent
    dummy_oc = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    dummy_oc.component.name = text
    dummy_co = dummy_oc.component
    
    box_3d = selected_entity.boundingBox
    sketches = dummy_co.sketches
    sketch = sketches.add(dummy_co.xYConstructionPlane)
    # FaceBox = sketch.boundingBox
    
    point1 = adsk.core.Point3D.create(box_3d.minPoint.x,box_3d.minPoint.y,0)
    point2 = adsk.core.Point3D.create(box_3d.maxPoint.x,box_3d.maxPoint.y,0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point1,point2)
    rec = sketch.profiles.item(0)

    # Extrusion
    extrudes = dummy_co.features.extrudeFeatures

    distance = adsk.core.ValueInput.createByReal(box_3d.minPoint.z)
    extrude1 = extrudes.addSimple(rec, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation) 

    distance2 = adsk.core.ValueInput.createByReal(box_3d.maxPoint.z)
    extrude2 = extrudes.addSimple(rec, distance2, 0) 

    dummy_co.opacity = 0.5
    dummy_oc.isGrounded=True



# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
