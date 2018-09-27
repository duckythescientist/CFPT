# Copy-From Paste-To
A Sublime Text 3 plugin to provide copy-from and paste-to options

## Copy-From

* Normal (standard text)
* Current Encoding (actual bytes)
* Hex Pairs
* Binary Octets
* Base64
* URL Encoded
* \x escaped

## Paste-To

* Normal (standard text)
* Current Encoding (actual bytes)
* 0xHex
* Hex Pairs
* \x Escaped
* Safe ASCII With \x Escapes (zealous)
* Safe ASCII With \x Escapes (minimal)
* URL Encoded
* Base64
* C Array


## Installation
```
cd ~/.config/sublime-text-3/Packages/
git clone https://github.com/duckythescientist/CFPT
# possibly restart sublimetext
```


## Usage
1. Select a region of text
1. Right click
1. Select a "Copy-From" or "Paste-To" subitem
1. Profit?

## Files

### Context.sublime-menu
This is the JSONish file that inserts commands into the rightclick context menu.

### CFPT.py
This is where the magic happens

## Inner Workings
Internally, how it works is each of the "Copy-From" commands take the text selection and formats the text to raw 8-bit characters which are then placed into the system clipboard. The "Paste-To" commands read from the system clipboard, run a formatter, and write out the formatted string to each cursor/region in Sublime. Depending on the formatting, an internal bytearray buffer will be used instead of the clipboard. This lets the plugins have more exact control over the data.

If a CF or PT operation cannot complete (e.g. an odd number of hex characters selected when copying from hex pairs), the clipboard is untouched, and a popup with the traceback is shown. 