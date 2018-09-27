# Copy-From Paste-To
A Sublime Text 3 plugin to provide copy-from and paste-to options


Internall, how it works is each of the "Copy-From" commands take the text selection and formats the text to raw 8-bit characters which are then placed into the system clipboard. The "Paste-To" commands read from the system clipboard, run a formatter, and write out the formatted string to each cursor/region in Sublime. Because this uses the system clipboard and internally stores everything as raw 8-bit character strings, the "raw" commands for both CF and PT have the same function as standard copy and paste. 

If a CF or PT operation cannot complete (e.g. an odd number of hex characters selected when copying from hex pairs), the clipboard is untouched, and a popup with the traceback is shown. 

## Copy-From

* Raw
* Hex pairs
* Base64
* URL Encoded
* \x escaped

## Paste-To

* Raw
* 0xHex
* Hex pairs
* \x escaped
* Safe ASCII with \x
* URL Encoded
* Base64


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