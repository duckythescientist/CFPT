import sublime, sublime_plugin
import struct
import base64
import traceback
import urllib
import string
import codecs
import re
# from typing import Union

# byteslike = Union[bytes, bytearray]

# Bodge because nullbytes don't play nicely with the clipboard
clipboard_string_g = ""  # Holds our remembered clipboard string
clipboard_bytearray_g = None  # Holds our raw data
# use_clipboard_data_g = False  # True when using our buffer instead of the system's clipboard


"""Helper Funcs"""

hexchars = "0123456789abcdefABCDEF"
safe_printable = string.ascii_letters + string.digits


def b2s(b):
    """Converts a byte array to a string."""
    # return "".join(chr(x) for x in b)
    return b.decode("latin_1")

def s2b(s):
    """Converts a string to a byte array."""
    # return bytearray(ord(x) for x in s)
    return bytearray(s.encode("latin_1"))

def greedy_hex(text):
    """Return only the hex characters in a string."""
    return "".join(x for x in text if x in hexchars)




"""Parent classes and dummy"""

class CFPT_From(sublime_plugin.TextCommand):
    
    encoding = None

    def gettext(self):
        """Return the text in the highlighted region."""
        region = self.view.sel()[0]
        return self.view.substr(region) 

    # def is_enabled(self):
    #     """Disable command when no text selected."""
    #     return self.gettext() is not ""

    # def formatter(self, raw: str): -> Union[(str, byteslike), byteslike, str]
    def formatter(self, raw):
        """Override this for your custom formatters

        Depending on how your formatter runs, you can return one of
        many types of output. 

        Return a `str` if you know what your text should look like.

        Return a `bytes` or `bytearray` if you are returning data,
        and you are fine with the clipboard having a utf-8
        representation of your data.

        Return a tuple of `(str, bytes)` or `(str, bytearray)` if
        the raw data is most important but you still care what the
        string looks like.
        """
        return None 

    def run(self, edit):
        """Called when the plugin is called.

        Gets the selected text, formats it, and puts it in the clipboard
        """
        global use_clipboard_data_g
        global clipboard_string_g
        global clipboard_bytearray_g
        use_clipboard_data_g = False
        raw = self.gettext()
        self.encoding = self.view.encoding()
        if self.encoding == "Undefined":
            self.encoding = "utf_8"
        print("Encoding:", self.encoding)
        if raw is not "":  # Did we actually select text?
            try:
                ret = self.formatter(raw)  # Do the formatting
                if isinstance(ret, (tuple, list)):
                    use_clipboard_data_g = True
                    fstr, fdata = ret
                    fdata = bytearray(fdata)
                elif isinstance(ret, (bytes, bytearray)):
                    use_clipboard_data_g = True
                    fdata = bytearray(ret)
                    fstr = ret.decode("utf_8", errors="ignore")
                elif isinstance(ret, str):
                    fstr = ret
                    fdata = bytearray(ret, "utf_8")
            except:
                sublime.error_message(traceback.format_exc())
                fmt = fdata
            if fstr is not None and fdata is not None:  # Formatter returned valid text
                if b"\x00" in fdata:  # Null bytes don't work in clipboards
                    use_clipboard_data_g = True  # Use our custom buffer
                    print("Setting internal clipboard string")
                    sublime.error_message("Warning: \nNull byte in text. Don't rely on standard paste")
                clipboard_bytearray_g = fdata
                clipboard_string_g = fstr
                sublime.set_clipboard(fstr)
                # Now get the clipboard because sometimes it gets
                # mangled, and we want to know the current state
                # to compare against later
                clipboard_string_g = sublime.get_clipboard()


class CFPT_To(sublime_plugin.TextCommand):
    """Pastes text as ?"""

    encoding = None

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

    # def formatter(self, raw: bytearray): -> Union[str, bytes, bytearray]
    def formatter(self, raw):
        """Override this for your custom formatters

        If you don't return a `str` type, your bytes like object
        will be encoded with the view's encoding
        """
        return None

    def run(self, edit):
        """Called when the plugin is called.

        Grabs the clipboard, formats it, and puts it into the text area
        """
        global use_clipboard_data_g
        global clipboard_string_g
        global clipboard_bytearray_g

        self.encoding = self.view.encoding()
        if self.encoding == "Undefined":
            self.encoding = "utf_8"
        print("Encoding:", self.encoding)
        clip = sublime.get_clipboard()
        if clip != clipboard_string_g:
            print("Clipboard data changed")
            fdata = bytearray(clip, "utf_8")
        elif use_clipboard_data_g:
            fdata = clipboard_bytearray_g
        else:
            fdata = bytearray(clip, "utf_8")

        try:
            fmt = self.formatter(fdata)
            if isinstance(fmt, (bytes, bytearray)):
                fmt = fmt.decode(self.encoding)
        except:
            sublime.error_message(traceback.format_exc())
            fmt = None
        if fmt is not None:
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

class CfptFromNormalCommand(CFPT_From):
    """Raw"""
    def formatter(self, raw):
        return raw

class CfptFromCurrentEncodingCommand(CFPT_From):
    def formatter(self, raw):
        return bytearray(raw, self.encoding)

class CfptFromHexCommand(CFPT_From):
    """Hex pairs (ignores non-hex characters so comma/space separated is fine)"""
    def formatter(self, raw):
        h = greedy_hex(raw)
        braw = base64.b16decode(h, casefold=True)
        return braw

class CfptFromBase64Command(CFPT_From):
    """Base64 Decode"""
    def formatter(self, raw):
        raw = re.sub(r"[^a-zA-Z0-9+/=]+", "", raw)
        print(raw)
        braw = base64.b64decode(raw)
        print(braw)
        return braw

class CfptFromUrlencodeCommand(CFPT_From):
    """URL Decode"""
    def formatter(self, raw):
        return urllib.parse.unquote_to_bytes(raw)

class CfptFromSlashxCommand(CFPT_From):
    """\\x?? escapes in string"""
    def formatter(self, raw):
        def xescape(match):
            v = match.group(1)
            return chr(int(v,16))
        ret = re.sub(r"\\x([0-9a-fA-F]{2})", xescape, raw)
        return ret.encode("latin_1")

class CfptFromBinaryCommand(CFPT_From):
    """Binary octets (ignores non-binary characters so comma/space separated is fine)"""
    def formatter(self, raw):
        b = "".join(x for x in raw if x in "01")
        raw = bytearray(int(b[i:i+8], 2) for i in range(0, len(b), 8))
        return raw


"""
Paste To

Make more of these
"""

class CfptToNormalCommand(CFPT_To):
    """Raw"""
    def formatter(self, raw):
        return raw.decode("utf-8")

class CfptToDirectEncodingCommand(CFPT_To):
    """Raw"""
    def formatter(self, raw):
        return raw

class CfptToZxhexCommand(CFPT_To):
    """0x??????"""
    def formatter(self, raw):
        enc = "0x" + base64.b16encode(raw).decode("ascii")
        return enc

class CfptToHexpairsCommand(CFPT_To):
    """Hex pairs"""
    def formatter(self, raw):
        enc = base64.b16encode(raw).decode("ascii")
        return enc

class CfptToSlashxCommand(CFPT_To):
    """\\x??\\x??\\x??"""
    def formatter(self, raw):
        enc = "".join("\\x%02X" % x for x in raw)
        return enc

class CfptToSlashxsafeCommand(CFPT_To):
    """\\x?? escape anything non-alphanumeric"""
    def formatter(self, raw):
        enc = "".join(chr(x) if chr(x) in safe_printable else "\\x%02X" % x for x in raw)
        return enc

class CfptToSlashxminimalCommand(CFPT_To):
    """\\x?? escape anything non-printable"""
    def formatter(self, raw):
        enc = "".join(chr(x) if chr(x) in string.printable else "\\x%02X" % x for x in raw)
        return enc

class CfptToUrlencodeCommand(CFPT_To):
    """URL Encode"""
    def formatter(self, raw):
        return urllib.parse.quote_from_bytes(raw)

class CfptToBase64Command(CFPT_To):
    """Base64 Encode"""
    def formatter(self, raw):
        return base64.b64encode(raw)

class CfptToCarrayCommand(CFPT_To):
    """0x??, 0x??, 0x?? C-style array"""
    def formatter(self, raw):
        return ", ".join("0x%02X" % x for x in raw)



"""
test strings

\x41\xab\xCD

ABCDEF

aoeu%AB%CDsnth

aGVsbG8sIHdvcmxk
"""
