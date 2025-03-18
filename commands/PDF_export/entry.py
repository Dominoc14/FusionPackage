import adsk.core, traceback
import os
from ...lib import fusion360utils as futil
from ... import config
import time
app = adsk.core.Application.get()
ui = app.userInterface


# Command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_PDF_export'
CMD_NAME = 'PDF_export'
CMD_Description = 'Export all drawing in the active folder to PDF'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Location of the command
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tab_id
TAB_NAME = config.tab_name
PANEL_ID = config.file_export_id
PANEL_NAME = config.file_export_name
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
    
    # Create the UI box
    inputs = args.command.commandInputs

    # Create the title of the UI box
    title_box = inputs.addTextBoxCommandInput('title_box', '', 'PDF export', 1, True)

    text_box_message = "You are about to save as PDF <b>all the drawing</b> contained in the open directory. <br> Once you click OK, you will have to choose where you want to save the PDF "
    text_box_input = inputs.addTextBoxCommandInput('text_box_input', 'Text Box', text_box_message, 2, True)
    text_box_input.isFullWidth = True
    
    # Create a selection input, apply filters and set the selection limits
    Open_PDF_input = inputs.addBoolValueInput('Open_PDF_input', 'Open PDF', True, '', False)
    Open_PDF_input.tooltip = "Check the box if you whant all the PDF to be open"

    # Get all components in the active design.
    product = app.activeProduct
    global design
    design = product
    global title
    title = 'Save Part As External'
    if not design:
        ui.messageBox('No active Fusion design', title)
        return

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    Open_PDF_input : adsk.core.SelectionCommandInput = inputs.itemById('Open_PDF_input')
    

    # Let users choose the folder to save the PDF files
    # Set styles of file dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'Path to save PDF' 
        
        # Show folder dialog
    result = folderDlg.showDialog()
    if result == adsk.core.DialogResults.DialogOK:
     _exportPDFFolder = folderDlg.folder
    else:
     return
        
        
        # get f2d datafile
    datafile = None
    file_to_save = len(app.data.activeFolder.dataFiles)
    for df in app.data.activeFolder.dataFiles:
         # log how many files are to be saved
         file_to_save -= 1
         msg = str(file_to_save)
         app.log(msg)
         # check datafile
         if df.fileExtension == "f2d": 
             datafile = df
             
             # open doc
             docs = app.documents
             drawDoc :adsk.drawing.DrawingDocument = docs.open(datafile)

            #  ##  -- ici on vérifiait dans le script que le document était bien ouvert, mais il semblerait que ce ne soit pas utile dans la version Add-in -- 
            #  # Tasks to be checked.
            #  targetTasks = [
            #     'DocumentFullyOpenedTask',
            #     'Nu::AnalyticsTask',
            #     'CheckValidationTask',
            #     'InvalidateCommandsTask'
            #     ]

            #         # check start task
            #  if not targetTasks[0] in getTaskList():
            #      ui.messageBox('Task not found : {}'.format(targetTasks[0]))
            #      return

            #     # Check the task and determine if the Document is Open.
                
            #  for targetTask in targetTasks:
            #      i=0
            #      while True:
            #          time.sleep(0.1)
            #          i += 1
            #          if not targetTask in getTaskList():
            #              break
            #          if i>=1000:
            #              ui.messageBox('Time out')
            #              return

                # export PDF
                
             expPDFpath = _exportPDFFolder + "/" + drawDoc.name + '.pdf'
             app.log(expPDFpath)
             draw :adsk.drawing.Drawing = drawDoc.drawing
             pdfExpMgr :adsk.drawing.DrawingExportManager = draw.exportManager

             pdfExpOpt :adsk.drawing.DrawingExportOptions = pdfExpMgr.createPDFExportOptions(expPDFpath)
             pdfExpOpt.openPDF = Open_PDF_input.value 
             pdfExpOpt.useLineWeights = True

             pdfExpMgr.execute(pdfExpOpt)

             # close doc
             drawDoc.close(False)


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

def getTaskList():
    adsk.doEvents()
    tasks = app.executeTextCommand(u'Application.ListIdleTasks').split('\n')
    return [s.strip() for s in tasks[2:-1]]

# a retirer plus tard 
def dumpMsg(msg :str):
    ui.palettes.itemById('TextCommands').writeText(str(msg))