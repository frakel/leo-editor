# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20171124080430.1: * @file ../commands/commanderOutlineCommands.py
#@@first
'''Outline commands that used to be defined in leoCommands.py'''
import leo.core.leoGlobals as g
#@+others
#@+node:ekr.20040412060927: ** c_oc.dumpOutline
@g.commander_command('dump-outline')
def dumpOutline(self, event=None):
    """ Dump all nodes in the outline."""
    c = self
    seen = {}
    print('')
    print('=' * 40)
    v = c.hiddenRootNode
    v.dump()
    seen[v] = True
    for p in c.all_positions():
        if p.v not in seen:
            seen[p.v] = True
            p.v.dump()
#@+node:ekr.20171124081846.1: ** c_oc.fullCheckOutline
@g.commander_command('check-outline')
def fullCheckOutline(self, event=None):
    '''
    Performs a full check of the consistency of a .leo file.

    As of Leo 5.1, Leo performs checks of gnx's and outline structure
    before writes and after reads, pastes and undo/redo.
    '''
    c = self
    return c.checkOutline(check_links=True)
#@+node:ekr.20031218072017.1548: ** c_oc.Cut & Paste Outlines
#@+node:ekr.20031218072017.1549: *3* c_oc.cutOutline
@g.commander_command('cut-node')
def cutOutline(self, event=None):
    '''Delete the selected outline and send it to the clipboard.'''
    c = self
    if c.canDeleteHeadline():
        c.copyOutline()
        c.deleteOutline("Cut Node")
        c.recolor()
#@+node:ekr.20031218072017.1550: *3* c_oc.copyOutline
@g.commander_command('copy-node')
def copyOutline(self, event=None):
    '''Copy the selected outline to the clipboard.'''
    # Copying an outline has no undo consequences.
    c = self
    c.endEditing()
    s = c.fileCommands.putLeoOutline()
    g.app.paste_c = c
    g.app.gui.replaceClipboardWith(s)
#@+node:ekr.20031218072017.1551: *3* c_oc.pasteOutline & helpers
# To cut and paste between apps, just copy into an empty body first, then copy to Leo's clipboard.

@g.commander_command('paste-node')
def pasteOutline(self, event=None,
    reassignIndices=True,
    redrawFlag=True,
    s=None,
    tempOutline=False, # True: don't make entries in the gnxDict.
    undoFlag=True
):
    '''
    Paste an outline into the present outline from the clipboard.
    Nodes do *not* retain their original identify.
    '''
    c = self
    if s is None:
        s = g.app.gui.getTextFromClipboard()
    pasteAsClone = not reassignIndices
    # commenting following block fixes #478
    #if pasteAsClone and g.app.paste_c != c:
    #    g.es('illegal paste-retaining-clones', color='red')
    #    g.es('only valid in same outline.')
    #    return
    undoType = 'Paste Node' if reassignIndices else 'Paste As Clone'
    c.endEditing()
    if not s or not c.canPasteOutline(s):
        return # This should never happen.
    isLeo = g.match(s, 0, g.app.prolog_prefix_string)
    vnodeInfoDict = computeVnodeInfoDict(c) if pasteAsClone else {}
    # create a *position* to be pasted.
    if isLeo:
        pasted = c.fileCommands.getLeoOutlineFromClipboard(s, reassignIndices, tempOutline)
    if not pasted:
        # 2016/10/06:
        # We no longer support pasting MORE outlines. Use import-MORE-files instead.
        return None
    if pasteAsClone:
        copiedBunchList = computeCopiedBunchList(c, pasted, vnodeInfoDict)
    else:
        copiedBunchList = []
    if undoFlag:
        undoData = c.undoer.beforeInsertNode(c.p,
            pasteAsClone=pasteAsClone, copiedBunchList=copiedBunchList)
    c.validateOutline()
    if not tempOutline:
        # Fix #427: Don't check for duplicate vnodes.
        c.checkOutline()
    c.selectPosition(pasted)
    pasted.setDirty()
    c.setChanged(True, redrawFlag=redrawFlag) # Prevent flash when fixing #387.
    # paste as first child if back is expanded.
    back = pasted.back()
    if back and back.hasChildren() and back.isExpanded():
        # 2011/06/21: fixed hanger: test back.hasChildren().
        pasted.moveToNthChildOf(back, 0)
    if pasteAsClone:
        # Set dirty bits for ancestors of *all* pasted nodes.
        # Note: the setDescendentsDirty flag does not do what we want.
        for p in pasted.self_and_subtree():
            p.setAllAncestorAtFileNodesDirty(
                setDescendentsDirty=False)
    if undoFlag:
        c.undoer.afterInsertNode(pasted, undoType, undoData)
    if redrawFlag:
        c.redraw(pasted)
        c.recolor()
    return pasted
#@+node:ekr.20050418084539.2: *4* def computeCopiedBunchList
def computeCopiedBunchList(c, pasted, vnodeInfoDict):
    '''Create a dict containing only copied vnodes.'''
    d = {}
    for p in pasted.self_and_subtree():
        d[p.v] = p.v
    aList = []
    for v in vnodeInfoDict:
        if d.get(v):
            bunch = vnodeInfoDict.get(v)
            aList.append(bunch)
    return aList
#@+node:ekr.20050418084539: *4* def computeVnodeInfoDict
def computeVnodeInfoDict(c):
    '''
    We don't know yet which nodes will be affected by the paste, so we remember
    everything. This is expensive, but foolproof.
    
    The alternative is to try to remember the 'before' values of nodes in the
    FileCommands read logic. Several experiments failed, and the code is very ugly.
    In short, it seems wise to do things the foolproof way.
    '''
    d = {}
    for v in c.all_unique_nodes():
        if v not in d:
            d[v] = g.Bunch(v=v, head=v.h, body=v.b)
    return d
#@+node:EKR.20040610130943: *3* c_oc.pasteOutlineRetainingClones
@g.commander_command('paste-retaining-clones')
def pasteOutlineRetainingClones(self, event=None):
    '''Paste an outline into the present outline from the clipboard.
    Nodes *retain* their original identify.'''
    c = self
    return c.pasteOutline(reassignIndices=False)
#@+node:ekr.20031218072017.2898: ** c_oc.Expand & contract commands
#@+node:ekr.20031218072017.2900: *3* c_oc.contract-all
@g.command('contract-all')
def contractAllHeadlinesCommand(self, event=None, redrawFlag=True):
    '''Contract all nodes in the outline.'''
    # The helper does all the work.
    c = self
    c.contractAllHeadlines(event=event,redrawFlag=redrawFlag)
#@+node:ekr.20080819075811.3: *3* c_oc.contractAllOtherNodes & helper
@g.commander_command('contract-all-other-nodes')
def contractAllOtherNodes(self, event=None):
    '''
    Contract all nodes except those needed to make the
    presently selected node visible.
    '''
    c = self
    leaveOpen = c.p
    for p in c.rootPosition().self_and_siblings():
        c.contractIfNotCurrent(c, p, leaveOpen)
    c.redraw()
#@+node:ekr.20080819075811.7: *4* def contractIfNotCurrent
def contractIfNotCurrent(c, p, leaveOpen):
    if p == leaveOpen or not p.isAncestorOf(leaveOpen):
        p.contract()
    for child in p.children():
        if child != leaveOpen and child.isAncestorOf(leaveOpen):
            c.contractIfNotCurrent(child, leaveOpen)
        else:
            for p2 in child.self_and_subtree():
                p2.contract()
#@+node:ekr.20031218072017.2901: *3* c_oc.contractNode
@g.commander_command('contract-node')
def contractNode(self, event=None):
    '''Contract the presently selected node.'''
    c = self; p = c.p
    p.contract()
    if p.isCloned():
        c.redraw() # A full redraw is necessary to handle clones.
    else:
        c.redraw_after_contract(p=p, setFocus=True)
#@+node:ekr.20040930064232: *3* c_oc.contractNodeOrGoToParent
@g.commander_command('contract-or-go-left')
def contractNodeOrGoToParent(self, event=None):
    """Simulate the left Arrow Key in folder of Windows Explorer."""
    trace = False and not g.unitTesting
    c, cc, p = self, self.chapterController, self.p
    parent = p.parent()
    redraw = False
    if trace: g.trace(p.h,
        'children:', p.hasChildren(),
        'expanded:', p.isExpanded(),
        'shouldBeExpanded:', c.shouldBeExpanded(p))
    # Bug fix: 2016/04/19: test p.v.isExpanded().
    if p.hasChildren() and (p.v.isExpanded() or p.isExpanded()):
        c.contractNode()
    elif parent and parent.isVisible(c):
        # New in Leo 4.9.1: contract all children first.
        if c.collapse_on_lt_arrow:
            for child in parent.children():
                if child.isExpanded():
                    child.contract()
                    redraw = True
        if cc and cc.inChapter and parent.h.startswith('@chapter '):
            if trace: g.trace('root is selected chapter', parent.h)
        else:
            if trace: g.trace('not an @chapter node', parent.h)
            c.goToParent()
    # This is a bit off-putting.
    # elif not parent and not c.hoistStack:
        # p = c.rootPosition()
        # while p:
            # if p.isExpanded():
                # p.contract()
                # redraw = True
            # p.moveToNext()
    if redraw:
        c.redraw()
#@+node:ekr.20031218072017.2902: *3* c_oc.contractParent
@g.commander_command('contract-parent')
def contractParent(self, event=None):
    '''Contract the parent of the presently selected node.'''
    c = self; p = c.p
    parent = p.parent()
    if not parent: return
    parent.contract()
    c.redraw_after_contract(p=parent)
#@+node:ekr.20031218072017.2903: *3* c_oc.expandAllHeadlines
@g.commander_command('expand-all')
def expandAllHeadlines(self, event=None):
    '''Expand all headlines.
    Warning: this can take a long time for large outlines.'''
    c = self
    p = c.rootPosition()
    while p:
        c.expandSubtree(p)
        p.moveToNext()
    c.redraw_after_expand(p=c.rootPosition(), setFocus=True)
    c.expansionLevel = 0 # Reset expansion level.
#@+node:ekr.20031218072017.2904: *3* c_oc.expandAllSubheads
@g.commander_command('expand-all-subheads')
def expandAllSubheads(self, event=None):
    '''Expand all children of the presently selected node.'''
    c = self; p = c.p
    if not p: return
    child = p.firstChild()
    c.expandSubtree(p)
    while child:
        c.expandSubtree(child)
        child = child.next()
    c.redraw(p, setFocus=True)
#@+node:ekr.20031218072017.2905: *3* c_oc.expandLevel1..9
@g.commander_command('expand-to-level-1')
def expandLevel1(self, event=None):
    '''Expand the outline to level 1'''
    self.expandToLevel(1)

@g.commander_command('expand-to-level-2')
def expandLevel2(self, event=None):
    '''Expand the outline to level 2'''
    self.expandToLevel(2)

@g.commander_command('expand-to-level-3')
def expandLevel3(self, event=None):
    '''Expand the outline to level 3'''
    self.expandToLevel(3)

@g.commander_command('expand-to-level-4')
def expandLevel4(self, event=None):
    '''Expand the outline to level 4'''
    self.expandToLevel(4)

@g.commander_command('expand-to-level-5')
def expandLevel5(self, event=None):
    '''Expand the outline to level 5'''
    self.expandToLevel(5)

@g.commander_command('expand-to-level-6')
def expandLevel6(self, event=None):
    '''Expand the outline to level 6'''
    self.expandToLevel(6)

@g.commander_command('expand-to-level-7')
def expandLevel7(self, event=None):
    '''Expand the outline to level 7'''
    self.expandToLevel(7)

@g.commander_command('expand-to-level-8')
def expandLevel8(self, event=None):
    '''Expand the outline to level 8'''
    self.expandToLevel(8)

@g.commander_command('expand-to-level-9')
def expandLevel9(self, event=None):
    '''Expand the outline to level 9'''
    self.expandToLevel(9)
#@+node:ekr.20031218072017.2906: *3* c_oc.expandNextLevel
@g.commander_command('expand-next-level')
def expandNextLevel(self, event=None):
    '''Increase the expansion level of the outline and
    Expand all nodes at that level or lower.'''
    c = self
    # Expansion levels are now local to a particular tree.
    if c.expansionNode != c.p:
        c.expansionLevel = 1
        c.expansionNode = c.p.copy()
    # g.trace(c.expansionLevel)
    self.expandToLevel(c.expansionLevel + 1)
#@+node:ekr.20031218072017.2907: *3* c_oc.expandNode
@g.commander_command('expand-node')
def expandNode(self, event=None):
    '''Expand the presently selected node.'''
    trace = False and not g.unitTesting
    c = self; p = c.p
    p.expand()
    if p.isCloned():
        if trace: g.trace('***redraw')
        c.redraw() # Bug fix: 2009/10/03.
    else:
        c.redraw_after_expand(p, setFocus=True)
#@+node:ekr.20040930064232.1: *3* c_oc.expandNodeAnd/OrGoToFirstChild
@g.commander_command('expand-and-go-right')
def expandNodeAndGoToFirstChild(self, event=None):
    """If a node has children, expand it if needed and go to the first child."""
    c = self; p = c.p
    if p.hasChildren():
        if p.isExpanded():
            c.selectPosition(p.firstChild())
        else:
            c.expandNode()
            # Fix bug 930726
            # expandNodeAndGoToFirstChild only expands or only goes to first child .
            c.selectPosition(p.firstChild())
    c.treeFocusHelper()

@g.commander_command('expand-or-go-right')
def expandNodeOrGoToFirstChild(self, event=None):
    """Simulate the Right Arrow Key in folder of Windows Explorer."""
    c = self; p = c.p
    if p.hasChildren():
        if not p.isExpanded():
            c.expandNode() # Calls redraw_after_expand.
        else:
            c.redraw_after_expand(p.firstChild(), setFocus=True)
#@+node:ekr.20060928062431: *3* c_oc.expandOnlyAncestorsOfNode
@g.commander_command('expand-ancestors-only')
def expandOnlyAncestorsOfNode(self, event=None, p=None):
    '''Contract all nodes in the outline.'''
    trace = False and not g.unitTesting
    c = self
    level = 1
    if p: c.selectPosition(p) # 2013/12/25
    root = c.p
    if trace: g.trace(root.h)
    for p in c.all_unique_positions():
        p.v.expandedPositions = []
        p.v.contract()
    for p in root.parents():
        if trace: g.trace('call p.expand', p.h, p._childIndex)
        p.expand()
        level += 1
    c.redraw(setFocus=True)
    c.expansionLevel = level # Reset expansion level.
#@+node:ekr.20031218072017.2908: *3* c_oc.expandPrevLevel
@g.commander_command('expand-prev-level')
def expandPrevLevel(self, event=None):
    '''Decrease the expansion level of the outline and
    Expand all nodes at that level or lower.'''
    c = self
    # Expansion levels are now local to a particular tree.
    if c.expansionNode != c.p:
        c.expansionLevel = 1
        c.expansionNode = c.p.copy()
    self.expandToLevel(max(1, c.expansionLevel - 1))
#@+node:ekr.20031218072017.2028: ** c_oc.hoist/dehoist/clearAllHoists
#@+node:ekr.20120308061112.9865: *3* c_oc.deHoist
@g.commander_command('de-hoist')
@g.commander_command('dehoist')
def dehoist(self, event=None):
    '''Undo a previous hoist of an outline.'''
    c = self
    if not c.p or not c.hoistStack:
        return
    # Don't de-hoist an @chapter node.
    if c.chapterController and c.p.h.startswith('@chapter '):
        if not g.unitTesting:
            g.es('can not de-hoist an @chapter node.',color='blue')
        return
    bunch = c.hoistStack.pop()
    p = bunch.p
    if bunch.expanded: p.expand()
    else: p.contract()
    c.setCurrentPosition(p)
    c.redraw()
    c.frame.clearStatusLine()
    c.frame.putStatusLine("De-Hoist: " + p.h)
    c.undoer.afterDehoist(p, 'DeHoist')
    g.doHook('hoist-changed', c=c)
#@+node:ekr.20120308061112.9866: *3* c_oc.clearAllHoists
def clearAllHoists(self):
    '''Undo a previous hoist of an outline.'''
    c = self
    c.hoistStack = []
    c.frame.putStatusLine("Hoists cleared")
    g.doHook('hoist-changed', c=c)
#@+node:ekr.20120308061112.9867: *3* c_oc.hoist
@g.commander_command('hoist')
def hoist(self, event=None):
    '''Make only the selected outline visible.'''
    c = self
    p = c.p
    if not p:
        return
    # Don't hoist an @chapter node.
    if c.chapterController and p.h.startswith('@chapter '):
        if not g.unitTesting:
            g.es('can not hoist an @chapter node.',color='blue')
        return
    # Remember the expansion state.
    bunch = g.Bunch(p=p.copy(), expanded=p.isExpanded())
    c.hoistStack.append(bunch)
    p.expand()
    c.redraw(p)
    c.frame.clearStatusLine()
    c.frame.putStatusLine("Hoist: " + p.h)
    c.undoer.afterHoist(p, 'Hoist')
    g.doHook('hoist-changed', c=c)
#@+node:ekr.20031218072017.1759: ** c_oc.Insert, Delete & Clone commands
#@+node:ekr.20031218072017.1762: *3* c_oc.clone
@g.commander_command('clone-node')
def clone(self, event=None):
    '''Create a clone of the selected outline.'''
    c = self; u = c.undoer; p = c.p
    if not p:
        return None
    undoData = c.undoer.beforeCloneNode(p)
    c.endEditing() # Capture any changes to the headline.
    clone = p.clone()
    dirtyVnodeList = clone.setAllAncestorAtFileNodesDirty()
    c.setChanged(True)
    if c.validateOutline():
        u.afterCloneNode(clone, 'Clone Node', undoData, dirtyVnodeList=dirtyVnodeList)
        c.redraw(clone)
        return clone # For mod_labels and chapters plugins.
    else:
        clone.doDelete()
        c.setCurrentPosition(p)
        return None
#@+node:ekr.20150630152607.1: *3* c_oc.cloneToAtSpot
@g.commander_command('clone-to-at-spot')
def cloneToAtSpot(self, event=None):
    '''
    Create a clone of the selected node and move it to the last @spot node
    of the outline. Create the @spot node if necessary.
    '''
    c = self; u = c.undoer; p = c.p
    if not p:
        return
    # 2015/12/27: fix bug 220: do not allow clone-to-at-spot on @spot node.
    if p.h.startswith('@spot'):
        g.es("can not clone @spot node", color='red')
        return
    last_spot = None
    for p2 in c.all_positions():
        if g.match_word(p2.h, 0, '@spot'):
            last_spot = p2.copy()
    if not last_spot:
        last = c.lastTopLevel()
        last_spot = last.insertAfter()
        last_spot.h = '@spot'
    undoData = c.undoer.beforeCloneNode(p)
    c.endEditing() # Capture any changes to the headline.
    clone = p.copy()
    clone._linkAsNthChild(last_spot,
                          n=last_spot.numberOfChildren(),
                          adjust=True)
    dirtyVnodeList = clone.setAllAncestorAtFileNodesDirty()
    c.setChanged(True)
    if c.validateOutline():
        u.afterCloneNode(clone,
                         'Clone Node',
                         undoData,
                         dirtyVnodeList=dirtyVnodeList)
        c.contractAllHeadlines()
        c.redraw()
        c.selectPosition(clone)
    else:
        clone.doDelete()
        c.setCurrentPosition(p)
#@+node:ekr.20141023154408.5: *3* c_oc.cloneToLastNode
@g.commander_command('clone-node-to-last-node')
def cloneToLastNode(self, event=None):
    '''
    Clone the selected node and move it to the last node.
    Do *not* change the selected node.
    '''
    c, p, u = self, self.p, self.undoer
    if not p: return
    prev = p.copy()
    undoData = c.undoer.beforeCloneNode(p)
    c.endEditing() # Capture any changes to the headline.
    clone = p.clone()
    last = c.rootPosition()
    while last and last.hasNext():
        last.moveToNext()
    clone.moveAfter(last)
    dirtyVnodeList = clone.setAllAncestorAtFileNodesDirty()
    c.setChanged(True)
    u.afterCloneNode(clone, 'Clone Node To Last', undoData, dirtyVnodeList=dirtyVnodeList)
    c.redraw(prev)
    # return clone # For mod_labels and chapters plugins.
#@+node:ekr.20031218072017.1193: *3* c_oc.deleteOutline
@g.commander_command('delete-node')
def deleteOutline(self, event=None, op_name="Delete Node"):
    """Deletes the selected outline."""
    c, u = self, self.undoer
    p = c.p
    if not p: return
    c.endEditing() # Make sure we capture the headline for Undo.
    if p.hasVisBack(c): newNode = p.visBack(c)
    else: newNode = p.next() # _not_ p.visNext(): we are at the top level.
    if not newNode: return
    undoData = u.beforeDeleteNode(p)
    dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
    p.doDelete(newNode)
    c.setChanged(True)
    u.afterDeleteNode(newNode, op_name, undoData, dirtyVnodeList=dirtyVnodeList)
    c.redraw(newNode)
    c.validateOutline()
#@+node:ekr.20071005173203.1: *3* c_oc.insertChild
@g.commander_command('insert-child')
def insertChild(self, event=None):
    '''Insert a node after the presently selected node.'''
    c = self
    return c.insertHeadline(event=event, op_name='Insert Child', as_child=True)
#@+node:ekr.20031218072017.1761: *3* c_oc.insertHeadline
@g.commander_command('insert-node')
def insertHeadlineCommand(self, event=None, op_name="Insert Node", as_child=False):
    '''Insert a node after the presently selected node.'''
    c = self
    c.insertHeadline(event=event)
#@+node:ekr.20130922133218.11540: *3* c_oc.insertHeadlineBefore (new in Leo 4.11)
@g.commander_command('insert-node-before')
def insertHeadlineBefore(self, event=None):
    '''Insert a node before the presently selected node.'''
    c, current, u = self, self.p, self.undoer
    op_name = 'Insert Node Before'
    if not current: return
    # Can not insert before the base of a hoist.
    if c.hoistStack and current == c.hoistStack[-1].p:
        g.warning('can not insert a node before the base of a hoist')
        return
    c.endEditing()
    undoData = u.beforeInsertNode(current)
    p = current.insertBefore()
    g.doHook('create-node', c=c, p=p)
    p.setDirty(setDescendentsDirty=False)
    dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
    c.setChanged(True)
    u.afterInsertNode(p, op_name, undoData, dirtyVnodeList=dirtyVnodeList)
    c.redrawAndEdit(p, selectAll=True)
    return p
#@+node:ekr.20080425060424.1: ** c_oc.Sort commands
#@+node:ekr.20050415134809: *3* c_oc.sortChildren
# New in Leo 4.7 final: this method no longer supports
# the 'cmp' keyword arg.

@g.commander_command('sort-children')
def sortChildren(self, event=None, key=None, reverse=False):
    '''Sort the children of a node.'''
    c = self; p = c.p
    if p and p.hasChildren():
        c.sortSiblings(p=p.firstChild(), sortChildren=True, key=key, reverse=reverse)
#@+node:ekr.20050415134809.1: *3* c_oc.sortSiblings
# New in Leo 4.7 final: this method no longer supports
# the 'cmp' keyword arg.

@g.commander_command('sort-siblings')
def sortSiblings(self, event=None, key=None, p=None, sortChildren=False,
                  reverse=False):
    '''Sort the siblings of a node.'''
    c = self; u = c.undoer
    if not p : p = c.p
    if not p: return
    c.endEditing()
    undoType = 'Sort Children' if sortChildren else 'Sort Siblings'
    parent_v = p._parentVnode()
    parent = p.parent()
    oldChildren = parent_v.children[:]
    newChildren = parent_v.children[:]
    if key is None:

        def lowerKey(self):
            return (self.h.lower())

        key = lowerKey
    newChildren.sort(key=key, reverse=reverse)
    if oldChildren == newChildren:
        return
    # 2010/01/20. Fix bug 510148.
    c.setChanged(True)
    # g.trace(g.listToString(newChildren))
    bunch = u.beforeSort(p, undoType, oldChildren, newChildren, sortChildren)
    parent_v.children = newChildren
    if parent:
        dirtyVnodeList = parent.setAllAncestorAtFileNodesDirty()
    else:
        dirtyVnodeList = []
    u.afterSort(p, bunch, dirtyVnodeList)
    # Sorting destroys position p, and possibly the root position.
    p = c.setPositionAfterSort(sortChildren)
    c.redraw(p)
#@+node:ekr.20031218072017.2913: ** c_oc.Goto commands
#@+node:ekr.20031218072017.1628: *3* c_oc.goNextVisitedNode
@g.commander_command('go-forward')
def goNextVisitedNode(self, event=None):
    '''Select the next visited node.'''
    c = self
    p = c.nodeHistory.goNext()
    if p:
        c.nodeHistory.skipBeadUpdate = True
        try:
            c.selectPosition(p)
        finally:
            c.nodeHistory.skipBeadUpdate = False
            c.redraw_after_select(p)
#@+node:ekr.20031218072017.1627: *3* c_oc.goPrevVisitedNode
@g.commander_command('go-back')
def goPrevVisitedNode(self, event=None):
    '''Select the previously visited node.'''
    c = self
    p = c.nodeHistory.goPrev()
    if p:
        c.nodeHistory.skipBeadUpdate = True
        try:
            c.selectPosition(p)
        finally:
            c.nodeHistory.skipBeadUpdate = False
            c.redraw_after_select(p)
#@+node:ekr.20031218072017.2914: *3* c_oc.goToFirstNode
@g.commander_command('goto-first-node')
def goToFirstNode(self, event=None):
    '''Select the first node of the entire outline.'''
    c = self
    p = c.rootPosition()
    c.selectPosition(p)
    c.expandOnlyAncestorsOfNode()
    c.redraw()
    c.treeSelectHelper(p)
#@+node:ekr.20051012092453: *3* c_oc.goToFirstSibling
@g.commander_command('goto-first-sibling')
def goToFirstSibling(self, event=None):
    '''Select the first sibling of the selected node.'''
    c = self; p = c.p
    if p.hasBack():
        while p.hasBack():
            p.moveToBack()
    c.treeSelectHelper(p)
#@+node:ekr.20070615070925: *3* c_oc.goToFirstVisibleNode
@g.commander_command('goto-first-visible-node')
def goToFirstVisibleNode(self, event=None):
    '''Select the first visible node of the selected chapter or hoist.'''
    c = self
    p = c.firstVisible()
    if p:
        c.selectPosition(p)
        c.expandOnlyAncestorsOfNode()
        c.redraw_after_select(p)
        c.treeSelectHelper(p)
#@+node:ekr.20031218072017.2915: *3* c_oc.goToLastNode
@g.commander_command('goto-last-node')
def goToLastNode(self, event=None):
    '''Select the last node in the entire tree.'''
    c = self
    p = c.rootPosition()
    while p and p.hasThreadNext():
        p.moveToThreadNext()
    c.selectPosition(p)
    c.treeSelectHelper(p)
    c.expandOnlyAncestorsOfNode()
    c.redraw()
#@+node:ekr.20051012092847.1: *3* c_oc.goToLastSibling
@g.commander_command('goto-last-sibling')
def goToLastSibling(self, event=None):
    '''Select the last sibling of the selected node.'''
    c = self; p = c.p
    if p.hasNext():
        while p.hasNext():
            p.moveToNext()
    c.treeSelectHelper(p)
#@+node:ekr.20050711153537: *3* c_oc.goToLastVisibleNode
@g.commander_command('goto-last-visible-node')
def goToLastVisibleNode(self, event=None):
    '''Select the last visible node of selected chapter or hoist.'''
    c = self
    p = c.lastVisible()
    if p:
        c.selectPosition(p)
        c.expandOnlyAncestorsOfNode()
        c.redraw_after_select(p)
        c.treeSelectHelper(p)
#@+node:ekr.20031218072017.2916: *3* c_oc.goToNextClone
@g.commander_command('goto-next-clone')
def goToNextClone(self, event=None):
    '''
    Select the next node that is a clone of the selected node.
    If the selected node is not a clone, do find-next-clone.
    '''
    c, p = self, self.p
    cc = c.chapterController; p = c.p
    if not p:
        return
    if not p.isCloned():
        c.findNextClone()
        return
    v = p.v
    p.moveToThreadNext()
    wrapped = False
    while 1:
        if p and p.v == v:
            break
        elif p:
            p.moveToThreadNext()
        elif wrapped:
            break
        else:
            wrapped = True
            p = c.rootPosition()
    if p:
        if cc:
            # Fix bug #252: goto-next clone activate chapter.
            # https://github.com/leo-editor/leo-editor/issues/252
            chapter = cc.getSelectedChapter()
            old_name = chapter and chapter.name
            new_name = cc.findChapterNameForPosition(p)
            if new_name == old_name:
                c.selectPosition(p)
                c.redraw_after_select(p)
            else:
                c.selectPosition(p)
                cc.selectChapterByName(new_name)
        else:
            c.selectPosition(p)
            c.redraw_after_select(p)
    else:
        g.blue('done')
#@+node:ekr.20071213123942: *3* c_oc.findNextClone
@g.commander_command('find-next-clone')
def findNextClone(self, event=None):
    '''Select the next cloned node.'''
    c = self; p = c.p; cc = c.chapterController
    if not p: return
    if p.isCloned():
        p.moveToThreadNext()
    flag = False
    while p:
        if p.isCloned():
            flag = True; break
        else:
            p.moveToThreadNext()
    if flag:
        if cc:
            # name = cc.findChapterNameForPosition(p)
            cc.selectChapterByName('main')
        c.selectPosition(p)
        c.redraw_after_select(p)
    else:
        g.blue('no more clones')
#@+node:ekr.20031218072017.2917: *3* c_oc.goToNextDirtyHeadline
@g.commander_command('goto-next-changed')
def goToNextDirtyHeadline(self, event=None):
    '''Select the node that is marked as changed.'''
    c = self; p = c.p
    if not p: return
    p.moveToThreadNext()
    wrapped = False
    while 1:
        if p and p.isDirty():
            break
        elif p:
            p.moveToThreadNext()
        elif wrapped:
            break
        else:
            wrapped = True
            p = c.rootPosition()
    if not p: g.blue('done')
    c.treeSelectHelper(p) # Sets focus.
#@+node:ekr.20031218072017.2918: *3* c_oc.goToNextMarkedHeadline
@g.commander_command('goto-next-marked')
def goToNextMarkedHeadline(self, event=None):
    '''Select the next marked node.'''
    c = self; p = c.p
    if not p: return
    p.moveToThreadNext()
    wrapped = False
    while 1:
        if p and p.isMarked():
            break
        elif p:
            p.moveToThreadNext()
        elif wrapped:
            break
        else:
            wrapped = True
            p = c.rootPosition()
    if not p: g.blue('done')
    c.treeSelectHelper(p) # Sets focus.
#@+node:ekr.20031218072017.2919: *3* c_oc.goToNextSibling
@g.commander_command('goto-next-sibling')
def goToNextSibling(self, event=None):
    '''Select the next sibling of the selected node.'''
    c = self; p = c.p
    c.treeSelectHelper(p and p.next())
#@+node:ekr.20031218072017.2920: *3* c_oc.goToParent
@g.commander_command('goto-parent')
def goToParent(self, event=None):
    '''Select the parent of the selected node.'''
    c = self; p = c.p
    c.treeSelectHelper(p and p.parent())
#@+node:ekr.20031218072017.2921: *3* c_oc.goToPrevSibling
@g.commander_command('goto-prev-sibling')
def goToPrevSibling(self, event=None):
    '''Select the previous sibling of the selected node.'''
    c = self; p = c.p
    c.treeSelectHelper(p and p.back())
#@+node:ekr.20031218072017.2993: *3* c_oc.selectThreadBack
@g.commander_command('goto-prev-node')
def selectThreadBack(self, event=None):
    '''Select the node preceding the selected node in outline order.'''
    c = self; p = c.p
    if not p: return
    p.moveToThreadBack()
    c.treeSelectHelper(p)
#@+node:ekr.20031218072017.2994: *3* c_oc.selectThreadNext
@g.commander_command('goto-next-node')
def selectThreadNext(self, event=None):
    '''Select the node following the selected node in outline order.'''
    c = self; p = c.p
    if not p: return
    p.moveToThreadNext()
    c.treeSelectHelper(p)
#@+node:ekr.20031218072017.2995: *3* c_oc.selectVisBack
@g.commander_command('goto-prev-visible')
def selectVisBack(self, event=None):
    '''Select the visible node preceding the presently selected node.'''
    # This has an up arrow for a control key.
    c, p = self, self.p
    if not p:
        return
    if c.canSelectVisBack():
        p.moveToVisBack(c)
        c.treeSelectHelper(p)
    else:
        c.endEditing() # 2011/05/28: A special case.
#@+node:ekr.20031218072017.2996: *3* c_oc.selectVisNext
@g.commander_command('goto-next-visible')
def selectVisNext(self, event=None):
    '''Select the visible node following the presently selected node.'''
    c, p = self, self.p
    if not p:
        return
    if c.canSelectVisNext():
        p.moveToVisNext(c)
        c.treeSelectHelper(p)
    else:
        c.endEditing() # 2011/05/28: A special case.
#@+node:ekr.20031218072017.2922: ** c_oc.Mark commands
#@+node:ekr.20090905110447.6098: *3* c_oc.cloneMarked
@g.commander_command('clone-marked-nodes')
def cloneMarked(self, event=None):
    """Clone all marked nodes as children of a new node."""
    c = self; u = c.undoer; p1 = c.p.copy()
    # Create a new node to hold clones.
    parent = p1.insertAfter()
    parent.h = 'Clones of marked nodes'
    cloned, n, p = [], 0, c.rootPosition()
    while p:
        # Careful: don't clone already-cloned nodes.
        if p == parent:
            p.moveToNodeAfterTree()
        elif p.isMarked() and p.v not in cloned:
            cloned.append(p.v)
            if 0: # old code
                # Calling p.clone would cause problems
                p.clone().moveToLastChildOf(parent)
            else: # New code.
                # Create the clone directly as a child of parent.
                p2 = p.copy()
                n = parent.numberOfChildren()
                p2._linkAsNthChild(parent, n, adjust=True)
            p.moveToNodeAfterTree()
            n += 1
        else:
            p.moveToThreadNext()
    if n:
        c.setChanged(True)
        parent.expand()
        c.selectPosition(parent)
        u.afterCloneMarkedNodes(p1)
    else:
        parent.doDelete()
        c.selectPosition(p1)
    if not g.unitTesting:
        g.blue('cloned %s nodes' % (n))
    c.redraw()
#@+node:ekr.20160502090456.1: *3* c_oc.copyMarked
@g.commander_command('copy-marked-nodes')
def copyMarked(self, event=None):
    """Copy all marked nodes as children of a new node."""
    c = self; u = c.undoer; p1 = c.p.copy()
    # Create a new node to hold clones.
    parent = p1.insertAfter()
    parent.h = 'Copies of marked nodes'
    copied, n, p = [], 0, c.rootPosition()
    while p:
        # Careful: don't clone already-cloned nodes.
        if p == parent:
            p.moveToNodeAfterTree()
        elif p.isMarked() and p.v not in copied:
            copied.append(p.v)
            p2 = p.copyWithNewVnodes(copyMarked=True)
            p2._linkAsNthChild(parent, n, adjust=True)
            p.moveToNodeAfterTree()
            n += 1
        else:
            p.moveToThreadNext()
    if n:
        c.setChanged(True)
        parent.expand()
        c.selectPosition(parent)
        u.afterCopyMarkedNodes(p1)
    else:
        parent.doDelete()
        c.selectPosition(p1)
    if not g.unitTesting:
        g.blue('copied %s nodes' % (n))
    c.redraw()
#@+node:ekr.20111005081134.15540: *3* c_oc.deleteMarked
@g.commander_command('delete-marked-nodes')
def deleteMarked(self, event=None):
    """Delete all marked nodes."""
    c = self; u = c.undoer; p1 = c.p.copy()
    undo_data, p = [], c.rootPosition()
    while p:
        if p.isMarked():
            undo_data.append(p.copy())
            next = p.positionAfterDeletedTree()
            p.doDelete()
            p = next
        else:
            p.moveToThreadNext()
    if undo_data:
        u.afterDeleteMarkedNodes(undo_data, p1)
        if not g.unitTesting:
            g.blue('deleted %s nodes' % (len(undo_data)))
        c.setChanged(True)
    # Don't even *think* about restoring the old position.
    c.contractAllHeadlines()
    c.selectPosition(c.rootPosition())
    c.redraw()
#@+node:ekr.20111005081134.15539: *3* c_oc.moveMarked & helper
@g.commander_command('move-marked-nodes')
def moveMarked(self, event=None):
    '''
    Move all marked nodes as children of a new node.
    This command is not undoable.
    Consider using clone-marked-nodes, followed by copy/paste instead.
    '''
    c = self
    p1 = c.p.copy()
    # Check for marks.
    for v in c.all_unique_nodes():
        if v.isMarked():
            break
    else:
        return g.warning('no marked nodes')
    result = g.app.gui.runAskYesNoDialog(c,
        'Move Marked Nodes?',
        message='move-marked-nodes is not undoable\nProceed?',
    )
    if result == 'no':
        return
    # Create a new *root* node to hold the moved nodes.
    # This node's position remains stable while other nodes move.
    parent = createMoveMarkedNode(c)
    assert not parent.isMarked()
    moved = []
    p = c.rootPosition()
    while p:
        assert parent == c.rootPosition()
        # Careful: don't move already-moved nodes.
        if p.isMarked() and not parent.isAncestorOf(p):
            moved.append(p.copy())
            next = p.positionAfterDeletedTree()
            p.moveToLastChildOf(parent)
                # This does not change parent's position.
            p = next
        else:
            p.moveToThreadNext()
    if moved:
        # Find a position p2 outside of parent's tree with p2.v == p1.v.
        # Such a position may not exist.
        p2 = c.rootPosition()
        while p2:
            if p2 == parent:
                p2.moveToNodeAfterTree()
            elif p2.v == p1.v:
                break
            else:
                p2.moveToThreadNext()
        else:
            # Not found.  Move to last top-level.
            p2 = c.lastTopLevel()
        parent.moveAfter(p2)
        # u.afterMoveMarkedNodes(moved, p1)
        if not g.unitTesting:
            g.blue('moved %s nodes' % (len(moved)))
        c.setChanged(True)
    # c.contractAllHeadlines()
        # Causes problems when in a chapter.
    c.selectPosition(parent)
    c.redraw()
#@+node:ekr.20111005081134.15543: *4* def createMoveMarkedNode
def createMoveMarkedNode(c):
    oldRoot = c.rootPosition()
    p = oldRoot.insertAfter()
    p.moveToRoot(oldRoot)
    c.setHeadString(p, 'Moved marked nodes')
    return p
#@+node:ekr.20031218072017.2923: *3* c_oc.markChangedHeadlines
@g.commander_command('mark-changed-items')
def markChangedHeadlines(self, event=None):
    '''Mark all nodes that have been changed.'''
    c = self; u = c.undoer; undoType = 'Mark Changed'
    current = c.p
    c.endEditing()
    u.beforeChangeGroup(current, undoType)
    for p in c.all_unique_positions():
        if p.isDirty() and not p.isMarked():
            bunch = u.beforeMark(p, undoType)
            c.setMarked(p)
            c.setChanged(True)
            u.afterMark(p, undoType, bunch)
    u.afterChangeGroup(current, undoType)
    if not g.unitTesting:
        g.blue('done')
    c.redraw_after_icons_changed()
#@+node:ekr.20031218072017.2924: *3* c_oc.markChangedRoots
def markChangedRoots(self, event=None):
    '''Mark all changed @root nodes.'''
    c = self; u = c.undoer; undoType = 'Mark Changed'
    current = c.p
    c.endEditing()
    u.beforeChangeGroup(current, undoType)
    for p in c.all_unique_positions():
        if p.isDirty() and not p.isMarked():
            s = p.b
            flag, i = g.is_special(s, 0, "@root")
            if flag:
                bunch = u.beforeMark(p, undoType)
                c.setMarked(p)
                c.setChanged(True)
                u.afterMark(p, undoType, bunch)
    u.afterChangeGroup(current, undoType)
    if not g.unitTesting:
        g.blue('done')
    c.redraw_after_icons_changed()
#@+node:ekr.20031218072017.2928: *3* c_oc.markHeadline
@g.commander_command('mark')
def markHeadline(self, event=None):
    '''Toggle the mark of the selected node.'''
    c = self; u = c.undoer; p = c.p
    if not p: return
    c.endEditing()
    undoType = 'Unmark' if p.isMarked() else 'Mark'
    bunch = u.beforeMark(p, undoType)
    if p.isMarked():
        c.clearMarked(p)
    else:
        c.setMarked(p)
    dirtyVnodeList = p.setDirty()
    c.setChanged(True)
    u.afterMark(p, undoType, bunch, dirtyVnodeList=dirtyVnodeList)
    c.redraw_after_icons_changed()
#@+node:ekr.20031218072017.2929: *3* c_oc.markSubheads
@g.commander_command('mark-subheads')
def markSubheads(self, event=None):
    '''Mark all children of the selected node as changed.'''
    c = self; u = c.undoer; undoType = 'Mark Subheads'
    current = c.p
    if not current: return
    c.endEditing()
    u.beforeChangeGroup(current, undoType)
    dirtyVnodeList = []
    for p in current.children():
        if not p.isMarked():
            bunch = u.beforeMark(p, undoType)
            c.setMarked(p)
            dirtyVnodeList2 = p.setDirty()
            dirtyVnodeList.extend(dirtyVnodeList2)
            c.setChanged(True)
            u.afterMark(p, undoType, bunch)
    u.afterChangeGroup(current, undoType, dirtyVnodeList=dirtyVnodeList)
    c.redraw_after_icons_changed()
#@+node:ekr.20031218072017.2930: *3* c_oc.unmarkAll
@g.commander_command('unmark-all')
def unmarkAll(self, event=None):
    '''Unmark all nodes in the entire outline.'''
    c = self; u = c.undoer; undoType = 'Unmark All'
    current = c.p
    if not current: return
    c.endEditing()
    u.beforeChangeGroup(current, undoType)
    changed = False
    p = None # To keep pylint happy.
    for p in c.all_unique_positions():
        if p.isMarked():
            bunch = u.beforeMark(p, undoType)
            # c.clearMarked(p) # Very slow: calls a hook.
            p.v.clearMarked()
            p.v.setDirty()
            u.afterMark(p, undoType, bunch)
            changed = True
    dirtyVnodeList = [p.v for p in c.all_unique_positions() if p.v.isDirty()]
    if changed:
        g.doHook("clear-all-marks", c=c, p=p, v=p)
        c.setChanged(True)
    u.afterChangeGroup(current, undoType, dirtyVnodeList=dirtyVnodeList)
    c.redraw_after_icons_changed()
#@+node:ekr.20031218072017.1766: ** c_oc.Move commands
#@+node:ekr.20031218072017.1767: *3* c_oc.demote
@g.commander_command('demote')
def demote(self, event=None):
    '''Make all following siblings children of the selected node.'''
    c = self; u = c.undoer
    p = c.p
    if not p or not p.hasNext():
        c.treeFocusHelper()
        return
    # Make sure all the moves will be valid.
    next = p.next()
    while next:
        if not c.checkMoveWithParentWithWarning(next, p, True):
            c.treeFocusHelper()
            return
        next.moveToNext()
    c.endEditing()
    parent_v = p._parentVnode()
    n = p.childIndex()
    followingSibs = parent_v.children[n + 1:]
    # g.trace('sibs2\n',g.listToString(followingSibs2))
    # Remove the moved nodes from the parent's children.
    parent_v.children = parent_v.children[: n + 1]
    # Add the moved nodes to p's children
    p.v.children.extend(followingSibs)
    # Adjust the parent links in the moved nodes.
    # There is no need to adjust descendant links.
    for child in followingSibs:
        child.parents.remove(parent_v)
        child.parents.append(p.v)
    p.expand()
    # Even if p is an @ignore node there is no need to mark the demoted children dirty.
    dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
    c.setChanged(True)
    u.afterDemote(p, followingSibs, dirtyVnodeList)
    c.redraw(p, setFocus=True)
    c.updateSyntaxColorer(p) # Moving can change syntax coloring.
#@+node:ekr.20031218072017.1768: *3* c_oc.moveOutlineDown
#@+at
# Moving down is more tricky than moving up; we can't move p to be a child of
# itself. An important optimization: we don't have to call
# checkMoveWithParentWithWarning() if the parent of the moved node remains the
# same.
#@@c

@g.commander_command('move-outline-down')
def moveOutlineDown(self, event=None):
    '''Move the selected node down.'''
    c = self; u = c.undoer; p = c.p
    if not p: return
    if not c.canMoveOutlineDown():
        if c.hoistStack: cantMoveMessage(c)
        c.treeFocusHelper()
        return
    inAtIgnoreRange = p.inAtIgnoreRange()
    parent = p.parent()
    next = p.visNext(c)
    while next and p.isAncestorOf(next):
        next = next.visNext(c)
    if not next:
        if c.hoistStack: cantMoveMessage(c)
        c.treeFocusHelper()
        return
    c.endEditing()
    undoData = u.beforeMoveNode(p)
    #@+<< Move p down & set moved if successful >>
    #@+node:ekr.20031218072017.1769: *4* << Move p down & set moved if successful >>
    if next.hasChildren() and next.isExpanded():
        # Attempt to move p to the first child of next.
        moved = c.checkMoveWithParentWithWarning(p, next, True)
        if moved:
            dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
            p.moveToNthChildOf(next, 0)
    else:
        # Attempt to move p after next.
        moved = c.checkMoveWithParentWithWarning(p, next.parent(), True)
        if moved:
            dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
            p.moveAfter(next)
    # Patch by nh2: 0004-Add-bool-collapse_nodes_after_move-option.patch
    if c.collapse_nodes_after_move and moved and c.sparse_move and parent and not parent.isAncestorOf(p):
        # New in Leo 4.4.2: contract the old parent if it is no longer the parent of p.
        parent.contract()
    #@-<< Move p down & set moved if successful >>
    if moved:
        if inAtIgnoreRange and not p.inAtIgnoreRange():
            # The moved nodes have just become newly unignored.
            p.setDirty() # Mark descendent @thin nodes dirty.
        else: # No need to mark descendents dirty.
            dirtyVnodeList2 = p.setAllAncestorAtFileNodesDirty()
            dirtyVnodeList.extend(dirtyVnodeList2)
        c.setChanged(True)
        u.afterMoveNode(p, 'Move Down', undoData, dirtyVnodeList)
    c.redraw(p, setFocus=True)
    c.updateSyntaxColorer(p) # Moving can change syntax coloring.
#@+node:ekr.20031218072017.1770: *3* c_oc.moveOutlineLeft
@g.commander_command('move-outline-left')
def moveOutlineLeft(self, event=None):
    '''Move the selected node left if possible.'''
    c = self; u = c.undoer; p = c.p
    if not p: return
    if not c.canMoveOutlineLeft():
        if c.hoistStack: cantMoveMessage(c)
        c.treeFocusHelper()
        return
    if not p.hasParent():
        c.treeFocusHelper()
        return
    inAtIgnoreRange = p.inAtIgnoreRange()
    parent = p.parent()
    c.endEditing()
    undoData = u.beforeMoveNode(p)
    dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
    p.moveAfter(parent)
    if inAtIgnoreRange and not p.inAtIgnoreRange():
        # The moved nodes have just become newly unignored.
        p.setDirty() # Mark descendent @thin nodes dirty.
    else: # No need to mark descendents dirty.
        dirtyVnodeList2 = p.setAllAncestorAtFileNodesDirty()
        dirtyVnodeList.extend(dirtyVnodeList2)
    c.setChanged(True)
    u.afterMoveNode(p, 'Move Left', undoData, dirtyVnodeList)
    # Patch by nh2: 0004-Add-bool-collapse_nodes_after_move-option.patch
    if c.collapse_nodes_after_move and c.sparse_move: # New in Leo 4.4.2
        parent.contract()
    c.redraw(p, setFocus=True)
    c.recolor() # Moving can change syntax coloring.
#@+node:ekr.20031218072017.1771: *3* c_oc.moveOutlineRight
@g.commander_command('move-outline-right')
def moveOutlineRight(self, event=None):
    '''Move the selected node right if possible.'''
    c = self; u = c.undoer; p = c.p
    if not p: return
    if not c.canMoveOutlineRight(): # 11/4/03: Support for hoist.
        if c.hoistStack: cantMoveMessage(c)
        c.treeFocusHelper()
        return
    back = p.back()
    if not back:
        c.treeFocusHelper()
        return
    if not c.checkMoveWithParentWithWarning(p, back, True):
        c.treeFocusHelper()
        return
    c.endEditing()
    undoData = u.beforeMoveNode(p)
    dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
    n = back.numberOfChildren()
    p.moveToNthChildOf(back, n)
    # Moving an outline right can never bring it outside the range of @ignore.
    dirtyVnodeList2 = p.setAllAncestorAtFileNodesDirty()
    dirtyVnodeList.extend(dirtyVnodeList2)
    c.setChanged(True)
    u.afterMoveNode(p, 'Move Right', undoData, dirtyVnodeList)
    # g.trace(p)
    c.redraw(p, setFocus=True)
    c.recolor()
#@+node:ekr.20031218072017.1772: *3* c_oc.moveOutlineUp
@g.commander_command('move-outline-up')
def moveOutlineUp(self, event=None):
    '''Move the selected node up if possible.'''
    trace = False and not g.unitTesting
    c = self; u = c.undoer; p = c.p
    if not p: return
    if not c.canMoveOutlineUp(): # Support for hoist.
        if c.hoistStack: cantMoveMessage(c)
        c.treeFocusHelper()
        return
    back = p.visBack(c)
    if not back:
        if trace: g.trace('no visBack')
        return
    inAtIgnoreRange = p.inAtIgnoreRange()
    back2 = back.visBack(c)
    c.endEditing()
    undoData = u.beforeMoveNode(p)
    dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
    moved = False
    #@+<< Move p up >>
    #@+node:ekr.20031218072017.1773: *4* << Move p up >>
    if trace:
        g.trace("visBack", back)
        g.trace("visBack2", back2)
        g.trace("back2.hasChildren", back2 and back2.hasChildren())
        g.trace("back2.isExpanded", back2 and back2.isExpanded())
    parent = p.parent()
    if not back2:
        if c.hoistStack: # hoist or chapter.
            limit, limitIsVisible = c.visLimit()
            assert limit
            if limitIsVisible:
                # canMoveOutlineUp should have caught this.
                g.trace('can not happen. In hoist')
            else:
                # g.trace('chapter first child')
                moved = True
                p.moveToFirstChildOf(limit)
        else:
            # p will be the new root node
            p.moveToRoot(oldRoot=c.rootPosition())
            moved = True
    elif back2.hasChildren() and back2.isExpanded():
        if c.checkMoveWithParentWithWarning(p, back2, True):
            moved = True
            p.moveToNthChildOf(back2, 0)
    else:
        if c.checkMoveWithParentWithWarning(p, back2.parent(), True):
            moved = True
            p.moveAfter(back2)
    # Patch by nh2: 0004-Add-bool-collapse_nodes_after_move-option.patch
    if c.collapse_nodes_after_move and moved and c.sparse_move and parent and not parent.isAncestorOf(p):
        # New in Leo 4.4.2: contract the old parent if it is no longer the parent of p.
        parent.contract()
    #@-<< Move p up >>
    if moved:
        if inAtIgnoreRange and not p.inAtIgnoreRange():
            # The moved nodes have just become newly unignored.
            dirtyVnodeList2 = p.setDirty() # Mark descendent @thin nodes dirty.
        else: # No need to mark descendents dirty.
            dirtyVnodeList2 = p.setAllAncestorAtFileNodesDirty()
        dirtyVnodeList.extend(dirtyVnodeList2)
        c.setChanged(True)
        u.afterMoveNode(p, 'Move Right', undoData, dirtyVnodeList)
    c.redraw(p, setFocus=True)
    c.updateSyntaxColorer(p) # Moving can change syntax coloring.
#@+node:ekr.20031218072017.1774: *3* c_oc.promote
@g.commander_command('promote')
def promote(self, event=None, undoFlag=True, redrawFlag=True):
    '''Make all children of the selected nodes siblings of the selected node.'''
    c = self; u = c.undoer; p = c.p
    if not p or not p.hasChildren():
        c.treeFocusHelper()
        return
    isAtIgnoreNode = p.isAtIgnoreNode()
    inAtIgnoreRange = p.inAtIgnoreRange()
    c.endEditing()
    parent_v = p._parentVnode()
    children = p.v.children
    # Add the children to parent_v's children.
    n = p.childIndex() + 1
    z = parent_v.children[:]
    parent_v.children = z[: n]
    parent_v.children.extend(children)
    parent_v.children.extend(z[n:])
    # Remove v's children.
    p.v.children = []
    # Adjust the parent links in the moved children.
    # There is no need to adjust descendant links.
    for child in children:
        child.parents.remove(p.v)
        child.parents.append(parent_v)
    c.setChanged(True)
    if undoFlag:
        if not inAtIgnoreRange and isAtIgnoreNode:
            # The promoted nodes have just become newly unignored.
            dirtyVnodeList = p.setDirty() # Mark descendent @thin nodes dirty.
        else: # No need to mark descendents dirty.
            dirtyVnodeList = p.setAllAncestorAtFileNodesDirty()
        u.afterPromote(p, children, dirtyVnodeList)
    if redrawFlag:
        c.redraw(p, setFocus=True)
        c.updateSyntaxColorer(p) # Moving can change syntax coloring.
#@+node:ekr.20071213185710: *3* c_oc.toggleSparseMove
@g.commander_command('toggle-sparse-move')
def toggleSparseMove(self, event=None):
    '''Toggle whether moves collapse the outline.'''
    c = self
    c.sparse_move = not c.sparse_move
    if not g.unitTesting:
        g.blue('sparse-move: %s' % c.sparse_move)
#@+node:ekr.20070420092425: ** def cantMoveMessage
def cantMoveMessage(c):
    h = c.rootPosition().h
    kind = 'chapter' if h.startswith('@chapter') else 'hoist'
    g.warning("can't move node out of", kind)
#@-others
#@-leo