
# Logseq2Obsidian

This simple tool attempts to converts a logseq graph to an Obsidian Vault

## Features

This is a non exhaustive list of "special" logseq markup converted to Obsidian format

- namespaces to directories
- page properties
- asset links

## Not supported

- Excalidraw (yet)


# Usage

How to Use:

1. Save: Save the code above as a Python file (e.g., logseq_to_obsidian.py).
1.  Backup: Seriously, back up your Logseq graph directory first!
1.  Run from Terminal:

```bash
python logseq_to_obsidian.py /path/to/your/logseq_graph /path/to/your/new_obsidian_vault
```

Replace /path/to/your/logseq_graph with the actual path to your Logseq directory (the one containing pages, assets, etc.).

Replace /path/to/your/new_obsidian_vault with the desired path for the new Obsidian vault directory. This directory should not exist unless you use the --force option.

4. Options:
  - --force or -f: Use this if the output directory already exists and you want to delete and replace it. Use with caution!
  - --verbose or -v: Shows more detailed debug messages about what the script is doing (useful for troubleshooting).

5. Review: Open the newly created directory as an Obsidian vault. Carefully check:
  - Are your pages there, including those previously in namespaces (now likely in folders)?
  - Do page properties appear correctly as YAML frontmatter at the top?
  - Do links to images/PDFs/etc. in your assets folder work? (Obsidian might use ![[assets/image.png]] or [text](assets/doc.pdf))
  - Do links to Excalidraw drawings work? Check if they appear as ![[Excalidraw/drawing.excalidraw]]. If not, you might need to manually edit the Markdown file to fix the link syntax based on where the .excalidraw file was copied.


This script provides a solid foundation for the conversion. Depending on the specifics and complexity of your Logseq graph, some manual adjustments in Obsidian might still be needed
