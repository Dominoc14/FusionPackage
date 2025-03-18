import adsk.core, traceback
import os
from ...lib import fusion360utils as futil
from ... import config
import time
app = adsk.core.Application.get()
ui = app.userInterface


# Command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_SaveAsExternal'
CMD_NAME = 'Save_as_external'
CMD_Description = 'Save part of the active component as external parts'

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
handlers = []


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

    # Get all components in the active design.
    product = app.activeProduct
    global design
    design = product
    global title
    title = 'Save Part As External'
    if not design:
        ui.messageBox('No active Fusion design', title)
        return
    
    inputs = args.command.commandInputs

    # Create the title of the UI box
    title_box = inputs.addTextBoxCommandInput('title_box', '', 'PCB Selection', 1, True)

    # Create a selection input, apply filters and set the selection limits
    selection_input = inputs.addSelectionInput('selection_input', 'Occurrence Selection', 'Select Occurence')
    selection_input.addSelectionFilter('Occurrences')
    selection_input.setSelectionLimits(0, 0)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    inputs = args.command.commandInputs
    selection_input : adsk.core.SelectionCommandInput = inputs.itemById('selection_input')
    selection = selection_input.selection(0)
    selected_entity = selection.entity
    # # Liste of all de components
    # components = design.allComponents
    # # Find the root component to exclude it
    root = design.rootComponent
    # # Make the list of all the component to save
    componentsToSave = []
    # for component in components:
    #     # Skip the root component.
    #     if root == component:
    #         continue
    #     componentsToSave.append(component)

    for j in range(0, selection_input.selectionCount):
        try: 
            selection = selection_input.selection(j)
            Occurences = selection.entity
            componentsToSave.append(Occurences.component)
        except:
            futil.log('Fail to find component')


    # Save as all the component
    SavedComponents = []
    Root_Name = root.name
    New_folder_name = Root_Name  + ' external part '
    Active_Folder = app.data.activeFolder
    Save_Folder = Active_Folder.dataFolders.add(New_folder_name)

    SavedComponents = save_components_event_driven(componentsToSave, Save_Folder)
    

    
    # componentsToDelete = componentsToSave
    # for component in componentsToDelete:
    #  if component.isValid == True:
    #     occurrences = root.allOccurrencesByComponent(component)
    #     name = component.name
    #     uniqueOccurrences = []
    #     for occurrence in occurrences:
                
    #         for k in range(0, len(uniqueOccurrences)):
    #             if occurrence is uniqueOccurrences[k]:
    #                 break
    #         if k == len(uniqueOccurrences):
    #             uniqueOccurrences.append(occurrence)

    #         # Delete them.
    #         for uniqueOccurrencesI in uniqueOccurrences:
    #             uniqueOccurrencesI.deleteMe()

    # #import file into curent design 
    # for file in Save_Folder.dataFiles:
    #        root.occurrences.addByInsert(file, adsk.core.Matrix3D.create(), True) 


    # Give feed back to user
    if SavedComponents == 0:
        msg = 'No component to save.'
    else:
        if SavedComponents > 1:
            msg = str(SavedComponents) + ' save component' + 's'
        else:
            msg = str(SavedComponents) + ' save component' + ' save'
        msg += '\n\n'
    ui.messageBox(msg, title)

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

def save_components_event_driven(components_to_save, save_folder):
    try:
        component_saved = 0
        for component in components_to_save:
                name = component.name
                component.saveCopyAs(name, save_folder, '', '')
                component_saved +=1
        return component_saved


    except Exception as e:
        ui.messageBox(f'Failed: {str(e)}')


