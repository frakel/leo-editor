# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20170107211202.1: * @file ../external/pyzo/highlighter.py
#@@first
#@+<< pyzo copyright >>
#@+node:ekr.20170108171824.1: ** << pyzo copyright >>
# Copyright (C) 2016, the Pyzo development team
#
# Pyzo is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.
#@-<< pyzo copyright >>
#@+<< highlighter imports >>
#@+node:ekr.20170107222425.1: ** << highlighter imports >>
from leo.core.leoQt import QtCore, QtGui
import leo.core.leoGlobals as g
ustr = g.ustr
from .parsers import BlockState
#@-<< highlighter imports >>
#@+others
#@+node:ekr.20170107211216.3: ** class BlockData
class BlockData(QtGui.QTextBlockUserData):
    """ Class to represent the data for a block.
    """
    #@+others
    #@+node:ekr.20170107211216.4: *3* __init__
    def __init__(self):
        QtGui.QTextBlockUserData.__init__(self)
        self.indentation = None
        self.fullUnderlineFormat = None
        self.tokens = []
    #@-others
# The highlighter should be part of the base class, because 
# some extensions rely on them (e.g. the indent guuides).
#@+node:ekr.20170107211216.5: ** class Highlighter
class Highlighter(QtGui.QSyntaxHighlighter):
    #@+others
    #@+node:ekr.20170107211216.6: *3* h.__init__
    def __init__(self, codeEditor, *args):
        # Set these *before* initing the base class.
        self._codeEditor = codeEditor
        QtGui.QSyntaxHighlighter.__init__(self,*args)
            # Generates call to rehighlight.
    #@+node:ekr.20170107211216.7: *3* h.getCurrentBlockUserData
    def getCurrentBlockUserData(self):
        """ getCurrentBlockUserData()
        
        Gets the BlockData object. Creates one if necesary.
        
        """
        bd = self.currentBlockUserData()
        if not isinstance(bd, BlockData):
            bd = BlockData()
            self.setCurrentBlockUserData(bd)
        return bd
    #@+node:ekr.20170107211216.8: *3* h.highlightBlock
    def highlightBlock(self, line): 
        """ highlightBlock(line)
        
        This method is automatically called when a line must be 
        re-highlighted.
        
        If the code editor has an active parser. This method will use
        it to perform syntax highlighting. If not, it will only 
        check out the indentation.
        
        """
        trace = False and not g.unitTesting
        # Make sure this is a Unicode Python string
        line = ustr(line)
        # Get previous state
        previousState = self.previousBlockState()
        # Get parser
        if hasattr(self._codeEditor, 'parser'):
            parser = self._codeEditor.parser()
        else:
            return ###
        # if trace: g.trace(repr(line))
        # Get function to get format
        nameToFormat = self._codeEditor.getStyleElementFormat
        fullLineFormat = None
        tokens = []
        if parser:
            self.setCurrentBlockState(0)
            tokens = list(parser.parseLine(line, previousState))
            # g.trace(len(tokens), 'tokens', tokens)
            for token in tokens :
                # Handle block state
                if isinstance(token, BlockState):
                    self.setCurrentBlockState(token.state)
                    if trace: g.trace('block state')
                else:
                    # Get format
                    try:
                        styleFormat = nameToFormat(token.name)
                        charFormat = styleFormat.textCharFormat
                    except KeyError:
                        g.trace('key error:', token.name)
                        continue
                    # Set format
                    # if trace: g.trace(token.name,charFormat)
                    self.setFormat(token.start,token.end-token.start,charFormat)
                    # Is this a cell?
                    if 1:
                        fullLineFormat = styleFormat
                    elif (
                        (fullLineFormat is None) and
                        styleFormat._parts.get('underline','') == 'full'
                    ):
                        fullLineFormat = styleFormat
        # Get user data
        bd = self.getCurrentBlockUserData()
        # Store token list for future use (e.g. brace matching)
        bd.tokens = tokens
        # Handle underlines
        bd.fullUnderlineFormat = fullLineFormat
        # Get the indentation setting of the editors
        indentUsingSpaces = True ### self._codeEditor.indentUsingSpaces()
        leadingWhitespace=line[:len(line)-len(line.lstrip())]
        if 1:
            bd.indentation = len(leadingWhitespace)
        elif '\t' in leadingWhitespace and ' ' in leadingWhitespace:
            #Mixed whitespace
            bd.indentation = 0
            format=QtGui.QTextCharFormat()
            format.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
            format.setUnderlineColor(QtCore.Qt.red)
            format.setToolTip('Mixed tabs and spaces')
            self.setFormat(0,len(leadingWhitespace),format)
        elif (
            ('\t' in leadingWhitespace and indentUsingSpaces) or
            (' ' in leadingWhitespace and not indentUsingSpaces)
        ):
            #Whitespace differs from document setting
            bd.indentation = 0
            format=QtGui.QTextCharFormat()
            format.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
            format.setUnderlineColor(QtCore.Qt.blue)
            format.setToolTip('Whitespace differs from document setting')
            self.setFormat(0,len(leadingWhitespace),format)
        else:
            # Store info for indentation guides
            # amount of tabs or spaces
            bd.indentation = len(leadingWhitespace)
    #@+node:ekr.20170108091854.1: *3* h.rehighlight (new)
    if 1:
        def rehighlight(self, p=None):
            '''Leo override, allowing the 'p' keyword arg.'''
            g.trace('(pyzo)', p and p.h)
            QtGui.QSyntaxHighlighter.rehighlight(self)
    #@-others
#@-others
#@@language python
#@@tabwidth -4
#@-leo