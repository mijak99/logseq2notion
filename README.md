
# Logseq2Obsidian

This simple tool attempts to converts a logseq graph to an Obsidian Vault

# Features

This is a non exhaustive list of "special" logseq markup converted to Obsidian format.

The tool makes a best effort to

- migrates page properties
- migrates page aliases
- When tags are used as Link to a page in Logseq, the page link is retained. 
- Retains asset links (embedded images, etc)
- Support for the Excalidraw plugin by haydenull  
    - If you have named/labelled your drawing in logseq-excalidraw, the conversion will retain your name as a page alias. 
    - This means your file is searchable as in logseq, but it's unfortunately still hard to browse for the diagram if you forget your labels 
- convert namespaces to directories (optional, see -c)


## Not supported

- whiteboards 
- numbered lists

# Usage

# Usage

How to Use:

1. Clone the repo
1. Run from Terminal:

> python logseq_to_obsidian.py /path/to/logseq-graph-dir -f -n /path/to/new/obsidian-vault

Open the new vault in Obsidian, and work from there.

For more details on usage:

> python logseq_to_obsidian.py --help



# Development notes

## File structure

- tests/testgraph - a graph used for testing
- tests/ : TODO write more unit tests
- docs/ : Some documentation/research 
- ouput-vault : Just a placeholder output dir for testing purposes 

## Testing

> python logseq_to_obsidian.py tests/testgraph/ -f output-vault/  -v -c


## TODO

- [x] Namespaces as a parameter -- when folders are used, links must also be adjusted
- [x] Excalidraw filenames (plugin alias) to Obsidian
    Has `excalidraw-plugin-alias:: My Cool Diagram` as a page property

- [x] Excalidraw render links / embeds
- [x] Tags can be used instead of page-links in logseq. If a tag is used in logseq, and the referred page exists in logseq - link it! 
- [ ] mermaid diagrams

### Someday...
- [ ] Track indentation levels, to better manage weird indentations
- [ ] Remove leading indents that does not start with a bullet [\-*]
- [ ] Blocks starting with 'id:: long-id-hash' -and references to them - might want some love
- [ ] Draws (built-in excalidraw)



