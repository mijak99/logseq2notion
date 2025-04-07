



# TL;DR

- extract the json from obsidian excalidraw files, ignoring the headers
- add source, type and version to the json object
- write it back to a .excaildraw file, with the headers stipulated by the obsidian plugin.

# Steps to convert logseq excalidraw  to Obsiodian 


## Logseq files

Logseq creates a .md page where the excalidraw is embedded in a json block

Note: 
- the embedded json is missing 3 mandatory fields, which must be added 
- source, type, and version
- These values seems to work, when added at the root level of the embedded json object. 
```yaml
source: "https://excalidraw.com"
type: "excalidraw"
version: 2
```


Example: 
> excalidraw-plugin:: true
>
>#+BEGIN_IMPORTANT
>
>  This file is used to store excalidraw information, >Please do not manually edit this file.
>
>#+END_IMPORTANT
>- {{renderer excalidraw-menu, >excalidraw-2025-04-07-11-42-51}}
- ```json
  {"elements":[{"id":"lbvYH5zTPMQOWaN16zHI0","type":"rectangle","x":688.3333129882812,"y":210.8333282470703,"width":247.5,"height":184.1666717529297,"angle":0,"strokeColor":"#1e1e1e","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":2,"strokeStyle":"solid","roughness":1,"opacity":100,"groupIds":[],"frameId":null,"roundness":{"type":3},"seed":1504885048,"version":15,"versionNonce":391936072,"isDeleted":false,"boundElements":[{"type":"text","id":"g1qjHfhbMremkq9HYMQ3N"}],"updated":1744018978868,"link":null,"locked":false},{"id":"g1qjHfhbMremkq9HYMQ3N","type":"text","x":725.333381652832,"y":290.41666412353516,"width":173.49986267089844,"height":25,"angle":0,"strokeColor":"#1e1e1e","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":2,"strokeStyle":"solid","roughness":1,"opacity":100,"groupIds":[],"frameId":null,"roundness":null,"seed":1334294328,"version":34,"versionNonce":888006216,"isDeleted":false,"boundElements":null,"updated":1744018986083,"link":null,"locked":false,"text":"This is a diagram","fontSize":20,"fontFamily":1,"textAlign":"center","verticalAlign":"middle","baseline":18,"containerId":"lbvYH5zTPMQOWaN16zHI0","originalText":"This is a diagram","lineHeight":1.25}],"files":{},"appState":{"gridSize":null,"viewBackgroundColor":"#ffffff","zoom":{"value":1},"offsetTop":20,"offsetLeft":0,"scrollX":0,"scrollY":0,"viewModeEnabled":false,"zenModeEnabled":false}}
  ```

## Obsidian files

Obsidian uses a similar approach to embed .excalidraw files, which are natively created by excalidraw

>---
>
>excalidraw-plugin: parsed
>tags: [excalidraw]
>
>---
>==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You >can decompress Drawing data with the command palette: 'Decompress current >Excalidraw file'. For more info check in plugin settings under 'Saving'
>
>
># Excalidraw Data
>
>## Text Elements
>This is a diagram ^zzT9aCwW
>
>%%
>## Drawing
>```compressed-json
>N4KAkARALgngDgUwgLgAQQQDwMYEMA2AlgCYBOuA7hADTgQBuCpAzoQPYB2KqATLZMzYBXUtiRoIACyhQ4z>ZAHoFAc0JRJQgEYA6bGwC2CgF7N6hbEcK4OCtptbErHALRY8RMpWdx8Q1TdIEfARcZgRmBShcZQUebQBObR>4aOiCEfQQOKGZuAG1wMFAwYogSbgh8TXoATQAJAFYjABUABQBZAEUAeQB1XAA5AEYANiNagEkABhTiyFhEc>sDsKI5l
>
>```

## General note


## General note

The embedded excalidraw data can be `json` or `compressed-json`, 
