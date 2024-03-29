# Script from https://github.com/AutodeskFusion360/DeleteEmptyComponents.git
# Fonction in the Clean CAD Panel
# Delete empty components from an assembly

import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# Command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_DeleteEmptyComponents'
CMD_NAME = 'Delete Empty Components'
CMD_Description = 'Delete Empty Components'

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
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    
    # Get all components in the active design.
    product = app.activeProduct
    global design
    design = product
    global title
    title = 'Delete Empty Components'
    if not design:
        ui.messageBox('No active Fusion design', title)
        return

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')


    components = design.allComponents

    # Find all of the empty components.
    # It is empty if it has no occurrences, bodies, featres, sketches, or construction.
    root = design.rootComponent
    componentsToDelete = []

    for component in components:

        # Skip the root component.
        if root == component:
            continue

        if len(component.occurrences) == 0 \
            and len(component.bRepBodies) == 0 \
            and len(component.features) == 0 \
            and len(component.sketches) == 0 \
            and len(component.constructionPlanes) == 0 \
            and len(component.constructionAxes) == 0 \
            and len(component.constructionPoints) == 0:

            componentsToDelete.append(component)

    # Delete all immediate occurrences of the empty components.
    deletedComponents = []
    global k
    k = 0
    for component in componentsToDelete:

        # Get the name first because deleting the final Occurrence will delete the Component.
        name = component.name

        # Build a list of unique immediate occurrences of the component.
        occurrences = root.allOccurrencesByComponent(component)
        uniqueOccurrences = []
        for occurrence in occurrences:
                
            for k in range(0, len(uniqueOccurrences)):
                if occurrence is uniqueOccurrences[k]:
                    break
            if k == len(uniqueOccurrences):
                uniqueOccurrences.append(occurrence)

        # Delete them.
        for uniqueOccurrencesI in uniqueOccurrences:
            uniqueOccurrencesI.deleteMe()

        deletedComponents.append(name)

    if len(deletedComponents) == 0:
        msg = 'No empty components found.'
    else:
        if len(deletedComponents) > 1:
            msg = str(len(deletedComponents)) + ' empty component' + 's'
        else:
            msg = str(len(deletedComponents)) + ' empty component' + ' deleted'
        msg += '\n\n'
        for deletedComponentI in deletedComponents:
            msg += '\n' + deletedComponentI

    ui.messageBox(msg, title)

        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
