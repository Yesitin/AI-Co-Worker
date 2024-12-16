from llama_index.core.tools import FunctionTool
from datetime import datetime
import textwrap
import os


# file path where there notes.txt will be saved
note_file = os.path.join("data", "notes.txt")


# function to create a notes.txt file based on input note
def save_note(note):
    if not os.path.exists(note_file):
        open(note_file, "w")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    # gives the file additionally a time stamp

    wrapped_note = textwrap.fill(note, width=80)                # to make breaks instead giving output into one single line

    with open(note_file, "a") as f:
        f.writelines([f"\n[{timestamp}] {wrapped_note}\n"])

    return "note saved"


# creates a engine for the agent with the save_note function 
note_engine = FunctionTool.from_defaults(
    fn = save_note,
    name = "note_saver",
    description = "this tool saves a text based note to a file for the user",
)