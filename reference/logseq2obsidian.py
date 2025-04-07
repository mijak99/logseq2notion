#!/usr/bin/env python3

# auto-converted by gemini from the perl version

import os
import shutil
import re
import argparse
import sys

# Comments from the original Perl script showing example usage:
# remove single dashes at the beginning of a line
# perl -pi.bak -e 's/^-\s*(.*)$/$1/' pages/scratch.md
#
# remove lines with only dashes
# perl -pi.bak -e 's/^\s*-\s*$//' pages/scratch.md

def convert_namespaces_to_directories(start_dir):
    """
    Recursively convert namespace-style filenames (using '___' as separator)
    into directory structures within the given start_dir.
    Example: file 'notes___project_a___task1.md' in start_dir
             becomes 'start_dir/notes/project_a/task1.md'
    """
    print(f"Starting directory conversion in '{start_dir}'...")
    files_moved = 0
    # Walk through the directory tree top-down
    for dirpath, _, filenames in os.walk(start_dir, topdown=True):
        # Important: Skip potential new directories created by previous iterations
        # This requires careful handling if files/dirs share base names,
        # but os.walk usually handles this okay if we process files first.
        # However, modifying the structure while walking can be tricky.
        # A safer approach might be to gather all moves first, then execute.
        # For simplicity matching the Perl script, we modify in place.

        for entry in filenames:
            # Split the filename by triple underscores
            parts = entry.split('___')

            # Process only if there's at least one '___' separator
            if len(parts) > 1:
                filename = parts.pop()  # The actual filename is the last part
                source_path = os.path.join(dirpath, entry)

                # Create the target directory path relative to the current dirpath
                # os.path.join handles the path separators correctly
                new_dir_relative_path = os.path.join(*parts)
                new_dir_full_path = os.path.join(dirpath, new_dir_relative_path)

                # Create the target directory(ies) if they don't exist
                try:
                    if not os.path.isdir(new_dir_full_path):
                        os.makedirs(new_dir_full_path)
                        # print(f"Created directory: {new_dir_full_path}") # Optional: verbose creation
                except OSError as e:
                    print(f"Error: Failed to create path: {new_dir_full_path} - {e}", file=sys.stderr)
                    continue # Skip this file if directory creation failed

                # Construct the full destination path
                target_path = os.path.join(new_dir_full_path, filename)

                # Move the file
                try:
                    shutil.move(source_path, target_path)
                    print(f"Moved {source_path} to {target_path}")
                    files_moved += 1
                except Exception as e:
                    print(f"Error: Failed to move {source_path} to {target_path}: {e}", file=sys.stderr)

    if files_moved == 0:
        print("No files with '___' separators found to move.")
    else:
        print(f"Finished directory conversion. Moved {files_moved} files.")


def convert_logseq_to_obsidian(file_path):
    """
    Convert Logseq properties (key:: value) at the beginning of a file
    to Obsidian/YAML front matter properties (key: value) enclosed in ---.
    """
    print(f"Converting Logseq properties to Obsidian properties in '{file_path}'")

    try:
        # Open the input file for reading
        with open(file_path, 'r', encoding='utf-8') as in_f:
            lines = in_f.readlines()
    except FileNotFoundError:
        print(f"Error: Cannot open '{file_path}' for reading: File not found.", file=sys.stderr)
        return
    except IOError as e:
        print(f"Error: Cannot open '{file_path}' for reading: {e}", file=sys.stderr)
        return

    converted_properties = []
    properties_found = False
    lines_to_keep_index = 0 # Index of the first line *not* part of the properties

    # Regex to match Logseq properties: key:: value
    # Allows optional whitespace around ::
    logseq_prop_re = re.compile(r'^\s*([^:]+?)\s*::\s*(.*)$')

    for i, line in enumerate(lines):
        match = logseq_prop_re.match(line)
        if match:
            key = match.group(1).strip() # Get key, remove leading/trailing whitespace
            value = match.group(2).strip() # Get value, remove leading/trailing whitespace
            # Format as YAML property: key: value
            converted_properties.append(f"{key}: {value}\n")
            properties_found = True
            lines_to_keep_index = i + 1 # Update index for content after properties
        # Check for empty lines or lines starting with '---' which might signal end of properties early
        elif line.strip() == '' or line.strip() == '---':
             # Allow empty lines within the property block, but stop if non-property line encountered
             # Let's follow the Perl logic: stop at the *first* non-matching line.
             pass # Continue processing potential properties below an empty line
        else:
            # Stop processing properties as soon as a non-matching line is found
            break

    # If properties were converted, construct the new list of lines
    if properties_found:
        final_lines = ["---\n"] + converted_properties + ["---\n"] + lines[lines_to_keep_index:]

        # Write the converted lines back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as out_f:
                out_f.writelines(final_lines)
            print(f"Successfully converted properties in '{file_path}'")
        except IOError as e:
            print(f"Error: Cannot open '{file_path}' for writing: {e}", file=sys.stderr)
    else:
        print(f"No Logseq properties found at the beginning of '{file_path}'. File not modified.")


def main():
    parser = argparse.ArgumentParser(
        description="Tool to convert Logseq file structures and properties.",
        formatter_class=argparse.RawTextHelpFormatter # Keep help formatting nice
    )
    parser.add_argument(
        '--convert-dirs',
        action='store_true',
        help='Convert namespace-style filenames (using "___") \nto directory structures in the current directory.'
    )
    parser.add_argument(
        '--convert-props',
        metavar='<file_path>',
        dest='convert_path', # Match Perl variable name somewhat
        help='Convert Logseq properties (key:: value) at the start of the specified file \nto Obsidian YAML front matter (--- key: value ---).'
    )

    # Add a check for no arguments if desired.
    # The original Perl script would just exit silently if no valid options given.
    # argparse handles the --help case automatically.
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    action_taken = False
    if args.convert_dirs:
        action_taken = True
        current_dir = os.getcwd()
        try:
             convert_namespaces_to_directories(current_dir)
        except Exception as e:
             print(f"An unexpected error occurred during directory conversion: {e}", file=sys.stderr)
             sys.exit(1) # Exit if the main action fails catastrophically


    if args.convert_path:
        action_taken = True
        # No need for explicit check if args.convert_path is defined,
        # argparse ensures it's either None or a string if the arg is provided.
        try:
            convert_logseq_to_obsidian(args.convert_path)
        except Exception as e:
             print(f"An unexpected error occurred during property conversion: {e}", file=sys.stderr)
             sys.exit(1) # Exit if the main action fails catastrophically

    # Optional: Inform the user if no action flag was provided (besides potential --help)
    # This case is already handled by the len(sys.argv) == 1 check above for initial call
    # if not action_taken and len(sys.argv) > 1: # Check if args were given but none were action flags
    #    print("No action specified. Use --convert-dirs or --convert-props.", file=sys.stderr)
    #    parser.print_help(sys.stderr)
    #    sys.exit(1)

if __name__ == "__main__":
    main()