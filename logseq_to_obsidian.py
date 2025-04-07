#!/usr/bin/env python3

# based on a one-shot generation from gemini

import logging
import os
import re
import shutil
import argparse
import json

from pathlib import Path


# --- Configuration ---
LOGSEQ_PAGES_DIR = "pages"
LOGSEQ_ASSETS_DIR = "assets"
LOGSEQ_JOURNALS_DIR = "journals"
LOGSEQ_EXCALIDRAW_DIR = "excalidraw" # Common name, adjust if yours differs

OBSIDIAN_ASSETS_DIR = "assets" # Standard Obsidian assets folder name
OBSIDIAN_EXCALIDRAW_DIR = "Excalidraw" # Common name for Obsidian Excalidraw plugin folder

OBSIDIAN_EXCALIDRAW_HEADER = '''---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'


# Excalidraw Data

## Text Elements

%%
## Drawing
'''


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Regex Patterns ---
# Logseq page properties (key:: value), potentially with leading spaces/tabs
# Captures key (group 1) and value (group 2)
# Assumes properties are at the start, possibly separated by blank lines
PROP_PATTERN = re.compile(r"^\s*([a-zA-Z0-9_-]+)::\s*(.*)")

# Links to assets in the standard Logseq assets folder
# Matches ![alt](../assets/...) or [text](../assets/...)
ASSET_LINK_PATTERN = re.compile(r"(!?\[.*?\]\()(\.\./" + re.escape(LOGSEQ_ASSETS_DIR) + r"/)(.*?\))")

# Embed-style links to assets ![alt](../assets/...) - Target for conversion to Obsidian embed
ASSET_EMBED_LINK_PATTERN = re.compile(r"(!\[.*?\]\()(\.\./" + re.escape(LOGSEQ_ASSETS_DIR) + r"/)(.*?\))")
# Simpler embed style like ![../assets/image.png] - Less common? Handled by below
OBSIDIAN_ASSET_EMBED_PATTERN_SIMPLE = re.compile(r"(!\[)(\.\./" + re.escape(LOGSEQ_ASSETS_DIR) + r"/)(.*?)\]")


# Links to Excalidraw files (common patterns)
# Matches [[../excalidraw/file.excalidraw]] or ![...](../excalidraw/...)
# Need to handle both markdown link and wikilink styles
EXCALIDRAW_LINK_MD_PATTERN = re.compile(r"(!?\[.*?\]\()(\.\./" + re.escape(LOGSEQ_EXCALIDRAW_DIR) + r"/)(.*?\))")
EXCALIDRAW_LINK_WIKI_PATTERN = re.compile(r"(!?\[\[)(\.\./" + re.escape(LOGSEQ_EXCALIDRAW_DIR) + r"/)(.*?)\]\]")
EXCALIDRAW_FILE_PATTERN = re.compile(r'^(excalidraw-\d\d\d\d-.*\.md$)')

migration_errors = [] # List to store errors for output to the user after migration

# --- Helper Functions ---

def convert_asset_link(match):
    """Converts a Logseq asset link relative path to Obsidian path."""
    prefix = match.group(1) # E.g., "![alt text](" or "[link text]("
    # group 2 is "../assets/"
    rest_of_link = match.group(3) # E.g., "image.png)"
    # Assume assets are moved to OBSIDIAN_ASSETS_DIR at the vault root
    new_path = f"{OBSIDIAN_ASSETS_DIR}/"
    logging.debug(f"Converting asset link: {match.group(0)} -> {prefix}{new_path}{rest_of_link}")
    return f"{prefix}{new_path}{rest_of_link}"

def convert_asset_embed_to_obsidian_embed(match):
    """Converts a Logseq asset embed ![...](../assets/...) to Obsidian ![[assets/...]] """
    # group 1 is "!["
    # group 2 is "../assets/"
    filename = match.group(3) # E.g., "image.png"
    new_embed = f"![[{OBSIDIAN_ASSETS_DIR}/{filename}]]"
    logging.debug(f"Converting asset embed: {match.group(0)} -> {new_embed}")
    return new_embed

def convert_excalidraw_link(match, link_type):
    """Converts a Logseq Excalidraw link relative path to Obsidian path."""
    if link_type == 'md':
        prefix = match.group(1) # E.g., "![alt text](" or "[link text]("
        # group 2 is "../excalidraw/"
        filename_and_suffix = match.group(3) # E.g., "drawing.excalidraw)"
        # Convert to Obsidian embed style ![[]]
        # Extract filename, remove trailing ')' if present
        filename = filename_and_suffix.rstrip(')')
        new_embed = f"![[{OBSIDIAN_EXCALIDRAW_DIR}/{filename}]]"
        logging.debug(f"Converting MD Excalidraw link: {match.group(0)} -> {new_embed}")
        return new_embed
    elif link_type == 'wiki':
        prefix = match.group(1) # E.g., "![[" or "[["
        # group 2 is "../excalidraw/"
        filename = match.group(3) # E.g., "drawing.excalidraw"
        # Ensure it's an embed style ![[...]]
        new_embed = f"![[{OBSIDIAN_EXCALIDRAW_DIR}/{filename}]]"
        logging.debug(f"Converting Wiki Excalidraw link: {match.group(0)} -> {new_embed}")
        return new_embed
    return match.group(0) # Should not happen


def remove_leading_bullets(line): 
    return re.sub(r'^\-\s*', '', line)

def replace_any_todo_items(line):
    line = re.sub(r'^((\s*)(-?\s)?)(TODO|NOW|WAITING|LATER)\W+(.*)$', r'\2- [ ] \5', line)
    line = re.sub(r'^((\s*)(-?\s)?)(DOING)\W+(.*)$', r'\2- [/] \5', line)
    line = re.sub(r'^((\s*)(-?\s)?)(DONE)\W+(.*)$', r'\2- [x] \5', line)
    return line

def from_logseq_line(line): 
    '''
    process a markdown line and removes logseq peculiarities, eg
    - unnecessary leading bullets 
    '''
    line = remove_leading_bullets(line) # must be called before todo_items
    line = replace_any_todo_items(line)
    return line


def process_logseq_excalidraw_file(logseq_graph_path, logseq_file_path, obsidian_excalidraw_path):
    """
    Reads a Logseq Markdown file containong an embedded excalidraw file, converts its content, and writes
    an excalidraw file to the Obsidian vault.
    """
    logging.info(f'Processing excalidraw file: {logseq_file_path}') 

    try:
        content = logseq_file_path.read_text(encoding='utf-8')
    except Exception as e:
        logging.error(f"Error reading file {logseq_file_path}: {e}")
        return
    
    json_pattern = r"json\n(.*?)\n"
    match = re.search(json_pattern, content, re.DOTALL)
    
    if match:
        json_string = match.group(1)

        # Create a new JSON object and add the "version", type, and source properties
        json_object = json.loads(json_string)
        json_object["type"] = "excalidraw"
        json_object["version"] = 2
        json_object["source"] = "https://excalidraw.com"

        # Convert back to string
        updated_json_string = json.dumps(json_object, indent=4)

        # --- Determine Output Path (Handle Namespaces -> Folders) ---
        obsidian_file_path = obsidian_excalidraw_path / logseq_file_path.name

        # Create parent directories if they don't exist
        obsidian_file_path.parent.mkdir(parents=True, exist_ok=True)


        final_content = f"{OBSIDIAN_EXCALIDRAW_HEADER}\n```json\n{updated_json_string}\n```\n"

        # --- Write the converted file ---
        try:
            obsidian_file_path.write_text(final_content, encoding='utf-8')
            logging.info(f"Converted: {logseq_file_path.name} -> {obsidian_file_path}")
        except Exception as e:
            logging.error(f"Error writing file {obsidian_file_path}: {e}")
    else: 
        logging.error(f'No json in the excalidraw diagram: {obsidian_file_path} ')

def process_logseq_md_file(logseq_file_path, obsidian_vault_path):
    """
    Reads a Logseq Markdown file, converts its content, and writes
    it to the corresponding location in the Obsidian vault.
    """

    logging.info(f"Converting: {logseq_file_path.name}")

    try:
        content = logseq_file_path.read_text(encoding='utf-8')
    except Exception as e:
        logging.error(f"Error reading file {logseq_file_path}: {e}")
        return

    lines = content.splitlines()
    properties = {}
    content_lines = []
    errors = []
    frontmatter_processed = False
    in_blockquote = False
    initial_block = True # Are we still in the potential frontmatter/property block at the top?

    # --- Extract properties and separate from content ---
    for i, line in enumerate(lines):
        if not frontmatter_processed:
            logging.debug(f"evaluating frontmatter on {line}")
            prop_match = PROP_PATTERN.match(line)
            if prop_match and initial_block:
                key = prop_match.group(1).strip()
                value = prop_match.group(2).strip()
                 # Basic handling for potential list values ( Obsidian syntax)
                if value.startswith('[') and value.endswith(']'):
                     # Attempt to make it a YAML list if comma-separated
                     items = [item.strip() for item in value[1:-1].split(',')]
                     if len(items) > 1:
                         properties[key] = items # Store as list for YAML
                     else:
                         properties[key] = value # Keep as string if not clearly a list
                elif value.lower() in ['true', 'false']:
                    properties[key] = bool(value.lower() == 'true')
                elif value.isdigit():
                     properties[key] = int(value)
                else:
                     # Simple string value, remove potential quotes if Obsidian might add them
                     properties[key] = value.strip('"\'')
                logging.debug(f"Found property: {key} -> {properties[key]}")
            elif line.strip() == "" and initial_block:
                # Allow blank lines between properties
                logging.debug(f"Skipping blank line: {line}")
                pass
            else:
                # First line that is not a property or blank line marks end of potential properties
                logging.debug(f"Frontmatter ending: {line}")

                initial_block = False
                frontmatter_processed = True
                content_lines.append(from_logseq_line(line))
        elif in_blockquote: 
            if line.startswith("```"): # end blockquote
                in_blockquote = False
            content_lines.append(line)

        else:
            # After frontmatter section, just append lines, with some conversions

            if line.startswith("```"): # start blockquote
                # no processing needed on this page or 
                in_blockquote = True
            elif line.startswith(">"): # inline blockquote
                pass # do no processing            


            # always put the line out
            content_lines.append(from_logseq_line(line))


    # --- Join content back (without properties) ---
    new_content = "\n".join(content_lines)

    # --- Convert Links ---
    # IMPORTANT: Process more specific embed conversions BEFORE general link conversions
    # Convert Logseq image embeds ![...](../assets/...) to Obsidian ![[assets/...]]
    new_content = OBSIDIAN_ASSET_EMBED_PATTERN_SIMPLE.sub(convert_asset_embed_to_obsidian_embed, new_content)
    # Convert other Logseq asset links [text](../assets/...) or ![...](../assets/...)
    new_content = ASSET_LINK_PATTERN.sub(convert_asset_link, new_content)

    # Convert Excalidraw Links (try both markdown and wiki styles)
    new_content = EXCALIDRAW_LINK_MD_PATTERN.sub(lambda m: convert_excalidraw_link(m, 'md'), new_content)
    new_content = EXCALIDRAW_LINK_WIKI_PATTERN.sub(lambda m: convert_excalidraw_link(m, 'wiki'), new_content)

    # --- Add YAML Frontmatter ---
    frontmatter = ""
    if properties:
        frontmatter += "---\n"
        for key, value in properties.items():
            # Basic YAML formatting (does not handle complex types perfectly)
            if isinstance(value, list):
                frontmatter += f"{key}:\n"
                for item in value:
                    frontmatter += f"  - {item}\n"
            elif isinstance(value, bool):
                 frontmatter += f"{key}: {str(value).lower()}\n" # YAML booleans are lowercase
            else:
                # Add quotes if value contains special characters like ':'? For simplicity, let's not overcomplicate.
                # Handle potential multi-line strings minimally by replacing newlines? No, keep simple.
                 frontmatter += f"{key}: {value}\n"

        frontmatter += "---\n\n" # Add separator and extra newline

    final_content = frontmatter + new_content.lstrip() # Remove leading whitespace before content


    # --- Determine Output Path (Handle Namespaces -> Folders) ---
    try:
        # Ensure paths are absolute before calculating relative path
        logging.debug("xxx file path stuff here")
        logging.debug(f"grap path: {logseq_graph_path}, file {logseq_file_path}")
        logseq_file_path = logseq_file_path.resolve()
        logging.debug(f"resolved to grap path: {logseq_graph_path}, file {logseq_file_path}")
        
        relative_path = logseq_file_path.relative_to(logseq_graph_path / LOGSEQ_PAGES_DIR)
        obsidian_file_path = obsidian_vault_path / relative_path
        logging.debug(f"relative path: {relative_path}")

        # If the filename of the logseq file contains triple underscores (___) in the name, 
        # treat those names as a folder separator in the destination vault
        # This is how logseq deals with namespaces
        if "___" in obsidian_file_path.name:
            parts = obsidian_file_path.name.split("___")
            obsidian_file_path = obsidian_file_path.parent / Path(*parts)


        # Create parent directories if they don't exist
        obsidian_file_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Write the converted file ---
        obsidian_file_path.write_text(final_content, encoding='utf-8')
        logging.info(f"Converted: {logseq_file_path.name} -> {obsidian_file_path}")

    except Exception as e:
        logging.error(f"Error when processing {logseq_file_path}: {e} - at line {e.__traceback__.tb_lineno}")
        migration_errors.append(f"- Error (line:{ {e.__traceback__.tb_lineno}}) processing {logseq_file_path}:\n  - {e}\n occured ")


# --- Main Conversion Logic ---

def convert_logseq_to_obsidian(logseq_graph_path, obsidian_vault_path, force_overwrite=False, clean=False):
    """Main function to orchestrate the conversion."""

    logseq_graph_path = Path(logseq_graph_path).resolve()
    logseq_graph_path = Path(os.path.relpath(logseq_graph_path, Path.cwd()))

    obsidian_vault_path = Path(obsidian_vault_path).resolve()
    
    # --- Input Validation ---
    if not logseq_graph_path.is_dir():
        logging.error(f"Logseq graph directory not found: {logseq_graph_path}")
        return False
    logseq_pages = logseq_graph_path / LOGSEQ_PAGES_DIR
    if not logseq_pages.is_dir():
        logging.error(f"Logseq 'pages' directory not found: {logseq_pages}")
        return False

    if obsidian_vault_path.exists():
        if force_overwrite:
            logging.warning(f"Output directory {obsidian_vault_path} exists. Overwriting.")
            try:
                if clean:
                    # remove the contents of the directory if --clean is specified
                    # but keep the ".obsidian" subdirectory if it exists
                    obsidian_config_path = obsidian_vault_path / ".obsidian"
                    if obsidian_config_path.is_dir(): # remove everything but the config directory
                        logging.info(f"Removing existing output directory (keeping config) {obsidian_vault_path}") 
                        for item in obsidian_vault_path.iterdir():
                            if item != obsidian_config_path:
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()  
                    else: # ok to remove everything
                        logging.info(f"Removing existing output directory {obsidian_vault_path}")
                        shutil.rmtree(obsidian_vault_path)

                    

            except Exception as e:
                logging.error(f"Could not remove existing output directory {obsidian_vault_path}: {e}")
                return False
        else:
            logging.error(f"Output directory {obsidian_vault_path} already exists. Use --force to overwrite.")
            return False

    # --- Create Obsidian Vault Structure ---
    try:
        obsidian_vault_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created Obsidian vault directory: {obsidian_vault_path}")
    except Exception as e:
        logging.error(f"Could not create Obsidian vault directory {obsidian_vault_path}: {e}")
        return False

    # --- Copy Assets ---
    logseq_assets = logseq_graph_path / LOGSEQ_ASSETS_DIR
    obsidian_assets = obsidian_vault_path / OBSIDIAN_ASSETS_DIR
    if logseq_assets.is_dir():
        try:
            shutil.copytree(logseq_assets, obsidian_assets)
            logging.info(f"Copied assets to {obsidian_assets}")
        except Exception as e:
            logging.error(f"Could not copy assets from {logseq_assets}: {e}")
            # Continue conversion even if assets fail? Yes.
    else:
        logging.warning(f"Logseq assets directory not found: {logseq_assets}")

    # --- Copy Journals ---
    logseq_journals = logseq_graph_path / LOGSEQ_JOURNALS_DIR
    obsidian_journals = obsidian_vault_path / LOGSEQ_JOURNALS_DIR # Keep same name usually
    if logseq_journals.is_dir():
        try:
            shutil.copytree(logseq_journals, obsidian_journals)
            logging.info(f"Copied journals to {obsidian_journals}")
        except Exception as e:
            logging.error(f"Could not copy journals from {logseq_journals}: {e}")
    else:
        logging.warning(f"Logseq journals directory not found: {logseq_journals}")

    # --- Copy Excalidraw Files ---
    logseq_excalidraw = logseq_graph_path / LOGSEQ_EXCALIDRAW_DIR
    obsidian_excalidraw = obsidian_vault_path / OBSIDIAN_EXCALIDRAW_DIR
    if logseq_excalidraw.is_dir():
        try:
            # Ensure target Excalidraw folder exists
            obsidian_excalidraw.mkdir(parents=True, exist_ok=True)
            shutil.copytree(logseq_excalidraw, obsidian_excalidraw, dirs_exist_ok=True) # Important for copying into existing dir
            logging.info(f"Copied Excalidraw files to {obsidian_excalidraw}")
        except Exception as e:
            logging.error(f"Could not copy Excalidraw files from {logseq_excalidraw}: {e}")
            logging.warning("Excalidraw file copying failed. Links in notes might be broken.")
    else:
        logging.warning(f"Logseq Excalidraw directory '{LOGSEQ_EXCALIDRAW_DIR}' not found: {logseq_excalidraw}")


    # --- Process Pages ---
    logging.info(f"Processing Logseq pages from: {logseq_pages}")
    file_count = 0
    for md_file in logseq_pages.rglob('*.md'): # rglob searches recursively
         if md_file.is_file():
            if EXCALIDRAW_FILE_PATTERN.match(md_file.name):
                 process_logseq_excalidraw_file(logseq_graph_path, md_file, obsidian_excalidraw)
            else:
                process_logseq_md_file(md_file, obsidian_vault_path)
            file_count += 1

    logging.info(f"Processed {file_count} Markdown files from the 'pages' directory.")
    logging.info("----- Conversion Summary -----")
    logging.info(f"Logseq Graph Source: {logseq_graph_path}")
    logging.info(f"Obsidian Vault Destination: {obsidian_vault_path}")
    logging.warning("Review your new Obsidian vault, especially:")
    logging.warning("- Links (internal, assets, Excalidraw)")
    logging.warning("- Page properties (frontmatter)")
    logging.warning("- Formatting and block structures")
    logging.warning("- Excalidraw drawings may need manual relinking if Logseq used complex plugin data.")

    # write all the errors to a file in the obsidian vault root, named migration-errors.md
    if migration_errors:
        error_file_path = obsidian_vault_path / "migration-errors.md"
        with error_file_path.open('w', encoding='utf-8') as error_file:
            for error in migration_errors:
                error_file.write(f"- {error}\n")
        logging.info(f"Errors logged to {error_file_path}")



    return True

# --- Command Line Interface ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a Logseq graph directory to an Obsidian vault.")
    parser.add_argument("logseq_dir", help="Path to the Logseq graph directory.")
    parser.add_argument("obsidian_dir", help="Path to the new directory for the Obsidian vault.")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite the output directory if it exists.")
    parser.add_argument("-c", "--clean", action="store_true", help="Remove the output directory if it exists.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging.")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Make global paths accessible within functions if needed (though passed is better)
    logseq_graph_path = Path(args.logseq_dir)
    # obsidian_vault_path is handled inside the main function

    convert_logseq_to_obsidian(args.logseq_dir, args.obsidian_dir, args.force, args.clean)