import sublime, sublime_plugin
import struct
import base64
import traceback
import urllib
import string
import codecs
import re


# Bodge because nullbytes don't play nicely with the clipboard
clipboard_string_g = ""  # Holds our clipboard data
use_clipboard_string_g = False  # True when using our buffer instead of the system's clipboard


"""Helper Funcs"""

hexchars = "0123456789abcdefABCDEF"
safe_printable = string.ascii_letters + string.digits


def b2s(b):
    """Converts a byte array to a string."""
    return "".join(chr(x) for x in b)

def s2b(s):
    """Converts a string to a byte array."""
    return bytearray(ord(x) for x in s)

def greedy_hex(text):
    """Return only the hex characters in a string."""
    return "".join(x for x in text if x in hexchars)




"""Parent classes and dummy"""

class CFPT_From(sublime_plugin.TextCommand):
    
    def gettext(self):
        """Return the text in the highlighted region."""
        region = self.view.sel()[0]
        return self.view.substr(region) 

    # def is_enabled(self):
    #     """Disable command when no text selected."""
    #     return self.gettext() is not ""

    def formatter(self, raw):
        """Override this for your custom formatters"""
        return None 

    def run(self, edit):
        """Called when the plugin is called.

        Gets the selected text, formats it, and puts it in the clipboard
        """
        global use_clipboard_string_g
        global clipboard_string_g
        use_clipboard_string_g = False
        raw = self.gettext()
        if raw is not "":  # Did we actually select text?
            try:
                fmt = self.formatter(raw)  # Do the formatting
            except:
                sublime.error_message(traceback.format_exc())
                fmt = None
            if fmt is not "" and fmt is not None:  # Formatter returned valid text
                if "\x00" in fmt:  # Null bytes don't work in clipboards
                    use_clipboard_string_g = True  # Use our custom buffer
                    clipboard_string_g = fmt 
                    print("Setting internal clipboard string")
                    sublime.error_message("Warning: \nNull byte in text. Using internal scratchpad ONCE.")
                else:
                    sublime.set_clipboard(fmt)


class CFPT_To(sublime_plugin.TextCommand):
    """Pastes text as ?"""

    def put(self, edit, s):
        """Puts 's' into the text area"""
        for region in self.view.sel():  # Allow for pasting to multiple regions
            if self.view.substr(region) is not "":  # Paste at the cursor
                self.view.replace(edit, region, s)
            else:  # Text is selected, so replace the selection
                self.view.insert(edit, region.begin(), s)


    # def is_enabled(self):
    #     """Disable command when nothing in clipboard."""
    #     return sublime.get_clipboard() is not ""

    def formatter(self, raw):
        """Override this for your custom formatters"""
        return None

    def run(self, edit):
        """Called when the plugin is called.

        Grabs the clipboard, formats it, and puts it into the text area
        """
        raw = sublime.get_clipboard()

        global use_clipboard_string_g
        global clipboard_string_g

        if use_clipboard_string_g:  # We are using our custom buffer
            raw = clipboard_string_g
            use_clipboard_string_g = False
            print("Getting internal clipboard string (length %d)"%len(raw))

        try:
            fmt = self.formatter(raw)
        except:
            sublime.error_message(traceback.format_exc())
            fmt = None
        if fmt is not "" and fmt is not None:
            self.put(edit, fmt)


class CfptTestFrom(CFPT_From):
    """Dummy just to grey out menu item when no text selected"""
    def run(self, edit):
        pass

class CfptTestTo(CFPT_To):
    """Dummy just to grey out menu item when clipboard is empty"""
    def run(self, edit):
        pass



"""It's not necessary to bother with error checking. The calling function will do that for you and report any exceptions in an error popup to the user. However, you may do manual error checking and reporting e.g. 
with sublime.error_message(str) if you wish to provide other information. 
"""



"""
Copy From

Make more of these
"""

class CfptFromRawCommand(CFPT_From):
    """Raw"""
    def formatter(self, raw):
        return raw

class CfptFromHexCommand(CFPT_From):
    """Hex pairs (ignores non-hex characters so comma/space separated is fine)"""
    def formatter(self, raw):
        h = greedy_hex(raw)
        braw = base64.b16decode(h, casefold=True)
        sraw = b2s(braw)
        # print(sraw)
        return sraw

class CfptFromBase64Command(CFPT_From):
    """Base64 Decode"""
    def formatter(self, raw):
        raw = re.sub(r"[^a-zA-Z0-9+/=]+", "", raw)
        print(raw)
        braw = base64.b64decode(raw)
        print(braw)
        sraw = b2s(braw)
        print(sraw)
        # print(raw)
        return sraw

class CfptFromUrlencodeCommand(CFPT_From):
    """URL Decode"""
    def formatter(self, raw):
        return b2s(urllib.parse.unquote_to_bytes(raw))

class CfptFromSlashxCommand(CFPT_From):
    """\\x?? escapes in string"""
    def formatter(self, raw):
        def xescape(match):
            v = match.group(1)
            return chr(int(v,16))
        return re.sub(r"\\x([0-9a-fA-F]{2})", xescape, raw)

class CfptFromBinaryCommand(CFPT_From):
    """Binary octets (ignores non-binary characters so comma/space separated is fine)"""
    def formatter(self, raw):
        b = "".join(x for x in raw if x in "01")
        sraw = "".join(chr(int(b[i:i+8],2)) for i in range(0,len(b),8))
        #sraw = b2s(braw)
        # print(sraw)
        return sraw


"""
Paste To

Make more of these
"""

class CfptToRawCommand(CFPT_To):
    """Raw"""
    def formatter(self, raw):
        return raw

class CfptToZxhexCommand(CFPT_To):
    """0x??????"""
    def formatter(self, raw):
        enc = "0x" + b2s(base64.b16encode(s2b(raw)))
        return enc

class CfptToHexpairsCommand(CFPT_To):
    """Hex pairs"""
    def formatter(self, raw):
        enc = b2s(base64.b16encode(s2b(raw)))
        return enc

class CfptToSlashxCommand(CFPT_To):
    """\\x??\\x??\\x??"""
    def formatter(self, raw):
        enc = "".join("\\x%02X"%ord(x) for x in raw)
        return enc

class CfptToSlashxsafeCommand(CFPT_To):
    """\\x?? escape anything non-alphanumeric"""
    def formatter(self, raw):
        enc = "".join(x if x in safe_printable else "\\x%02X"%ord(x) for x in raw)
        return enc

class CfptToSlashxminimalCommand(CFPT_To):
    """\\x?? escape anything non-printable"""
    def formatter(self, raw):
        enc = "".join(x if x in string.printable else "\\x%02X"%ord(x) for x in raw)
        return enc

class CfptToUrlencodeCommand(CFPT_To):
    """URL Encode"""
    def formatter(self, raw):
        return urllib.parse.quote_from_bytes(s2b(raw))

class CfptToBase64Command(CFPT_To):
    """Base64 Encode"""
    def formatter(self, raw):
        return b2s(base64.b64encode(s2b(raw)))

class CfptToCarrayCommand(CFPT_To):
    """0x??, 0x??, 0x?? C-style array"""
    def formatter(self, raw):
        return ", ".join("0x%02X"%ord(x) for x in raw)



"""
test strings

\x41\xab\xCD

ABCDEF

aoeu%AB%CDsnth

aGVsbG8sIHdvcmxk
"""
