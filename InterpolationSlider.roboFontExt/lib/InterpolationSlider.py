# coding: utf-8
import vanilla
from mojo.events import addObserver, removeObserver
from mojo.UI import CurrentGlyphWindow
import mojo.drawingTools as dt
from fontTools.pens.cocoaPen import CocoaPen
from AppKit import NSColor


"""
Interpolation Slider
by Andy Clymer, June 2018
"""

class InterpolationPreviewWindow(object):
    
    def __init__(self):
        
        self.currentGlyph = None
        self.window = None
        
        self.fonts = []
        self.fontNames = []
        
        self.glyph0 = None
        self.glyph1 = None
        self.compatibilityReport = None
        self.interpolatedGlyph = RGlyph()
        
        self.w = vanilla.FloatingWindow((250, 155), "Interpolation Slider")
        self.w.open()
        self.w.title = vanilla.TextBox((10, 10, -10, 25), "Masters:", sizeStyle="small")
        self.w.font0 = vanilla.PopUpButton((10, 25, -10, 25), [], callback=self.glyphChanged, sizeStyle="small")
        self.w.font1 = vanilla.PopUpButton((10, 50, -10, 25), [], callback=self.glyphChanged, sizeStyle="small")
        self.w.compatibilityText = vanilla.TextBox((-105, 83, 100, 25), u"Compatibility: ⚪️", sizeStyle="small")
        self.w.line = vanilla.HorizontalLine((5, 110, -5, 1))
        self.w.interpValue = vanilla.Slider((10, 120, -10, 25), callback=self.optionsChanged, minValue=0, maxValue=1)
        self.w.interpValue.set(0.5)
        self.w.bind("close", self.closed)
        
        self.collectFonts()
        self.glyphChanged(None)
        
        addObserver(self, "glyphChanged", "currentGlyphChanged")
        addObserver(self, "fontsChanged", "newFontDidOpen")
        addObserver(self, "fontsChanged", "fontDidOpen")
        addObserver(self, "fontsChanged", "fontDidClose")
        addObserver(self, "drawBkgnd", "drawBackground")
        addObserver(self, "drawPreview", "drawPreview")
    
    
    def closed(self, sender):
        if self.window:
            self.window.getGlyphView().refresh()
        if self.currentGlyph:
            self.currentGlyph.removeObserver(self, "Glyph.Changed")
            self.currentGlyph.removeObserver(self, "Glyph.ContoursChanged")
        removeObserver(self, "currentGlyphChanged")
        removeObserver(self, "newFontDidOpen")
        removeObserver(self, "fontDidOpen")
        removeObserver(self, "fontDidClose")
        removeObserver(self, "drawBackground")
        removeObserver(self, "drawPreview")
        
    
    def getFontName(self, font, fonts):
        # A helper to get the font name, starting with the preferred name and working back to the PostScript name
        # Make sure that it's not the same name as another font in the fonts list
        if font.info.openTypeNamePreferredFamilyName and font.info.openTypeNamePreferredSubfamilyName:
            name = "%s %s" % (font.info.openTypeNamePreferredFamilyName, font.info.openTypeNamePreferredSubfamilyName)
        elif font.info.familyName and font.info.styleName:
            name = "%s %s" % (font.info.familyName, font.info.styleName)
        elif font.info.fullName:
            name = font.info.fullName
        elif font.info.fullName:
            name = font.info.postscriptFontName
        else: name = "Untitled"
        # Add a number to the name if this name already exists
        if name in fonts:
            i = 2
            while name + " (%s)" % i in fonts:
                i += 1
            name = name + " (%s)" % i
        return name
        
        
    def collectFonts(self):
        # Hold aside the current font choices
        font0idx = self.w.font0.get()
        font1idx = self.w.font1.get()
        if not font0idx == -1:
            font0name = self.fontNames[font0idx]
        else: font0name = None
        if not font1idx == -1:
            font1name = self.fontNames[font1idx]
        else: font1name = None
        # Collect info on all open fonts
        self.fonts = AllFonts()
        self.fontNames = []
        for font in self.fonts:
            self.fontNames.append(self.getFontName(font, self.fontNames))
        # Update the popUpButtons
        self.w.font0.setItems(self.fontNames)
        self.w.font1.setItems(self.fontNames)
        # If there weren't any previous names, try to set the first and second items in the list
        if font0name == None:
            if len(self.fonts):
                self.w.font0.set(0)
        if font1name == None:
            if len(self.fonts)  >= 1:
                self.w.font1.set(1)
        # Otherwise, if there had already been fonts choosen before new fonts were loaded,
        # try to set the index of the fonts that were already selected
        if font0name in self.fontNames:
            self.w.font0.set(self.fontNames.index(font0name))
        if font1name in self.fontNames:
            self.w.font1.set(self.fontNames.index(font1name))
        
        
    def fontsChanged(self, info):
        self.collectFonts()
        self.glyphChanged(None)
        
        
    def glyphChanged(self, info):
        # Reset the glyph info
        self.glyph0 = None
        self.glyph1 = None
        self.compatibilityReport = None
        self.window = CurrentGlyphWindow()
        self.interpolatedGlyph.clear()
        # Remove any observers on the older CurrentGLyph and add them to the new one
        if self.currentGlyph:
            self.currentGlyph.removeObserver(self, "Glyph.Changed")
            self.currentGlyph.removeObserver(self, "Glyph.ContoursChanged")
        self.currentGlyph = CurrentGlyph()
        if self.currentGlyph:
            self.currentGlyph.addObserver(self, "optionsChanged", "Glyph.Changed")
            self.currentGlyph.addObserver(self, "optionsChanged", "Glyph.ContoursChanged")
        if self.currentGlyph:
            # Update the glyph info
            glyphName = self.currentGlyph.name
            master0idx = self.w.font0.get()
            master1idx = self.w.font1.get()
            master0 = self.fonts[master0idx]
            master1 = self.fonts[master1idx]
            if glyphName in master0:
                self.glyph0 = master0[glyphName]
            if glyphName in master1:
                self.glyph1 = master1[glyphName]
        # Update the interp compatibility report
        self.testCompatibility()
        # Update the view
        self.optionsChanged(None)
        
    
    def testCompatibility(self):
        status = u"⚪️"
        if self.window:
            if self.glyph0 == self.glyph1:
                status = u"⚪️"
            elif len(self.interpolatedGlyph.contours) > 0:
                status = u"✅"
            else: status = u"❌"
        self.w.compatibilityText.set(u"Compatibility: %s" % status)
                
        
    def optionsChanged(self, sender):
        if self.glyph0 and self.glyph1:
            # Interpolate
            self.interpolatedGlyph.clear()
            self.interpolatedGlyph.interpolate(self.w.interpValue.get(), self.glyph0, self.glyph1)
        self.testCompatibility()
        # ...and refresh the window
        if self.window:
            self.window.getGlyphView().refresh()
                
    
    def addPoints(self, pt0, pt1):
        return (pt0[0] + pt1[0], pt0[1] + pt1[1])
        
        
    def subtractPoints(self, pt0, pt1):
        return (pt0[0] - pt1[0], pt0[1] - pt1[1])
        
        
    def drawBkgnd(self, info):
        # Draw the interpolated glyph outlines
        scale = info["scale"]
        ptSize = 7 * scale
        if self.interpolatedGlyph:
            # Draw the glyph outline
            pen = CocoaPen(None)
            self.interpolatedGlyph.draw(pen)
            dt.fill(r=None, g=None, b=None, a=1)
            dt.stroke(r=0, g=0, b=0, a=0.4)
            dt.strokeWidth(2*scale)
            dt.save()
            dt.translate(self.currentGlyph.width)
            dt.drawPath(pen.path)
            dt.stroke(r=0, g=0, b=0, a=1)
            # Draw the points and handles
            for contour in self.interpolatedGlyph.contours:
                for bPoint in contour.bPoints:
                    inLoc = self.addPoints(bPoint.anchor, bPoint.bcpIn)
                    outLoc = self.addPoints(bPoint.anchor, bPoint.bcpOut)
                    dt.line(inLoc, bPoint.anchor)
                    dt.line(bPoint.anchor, outLoc)
                    dt.fill(r=1, g=1, b=1, a=1)    
                    dt.oval(bPoint.anchor[0] - (ptSize*0.5), bPoint.anchor[1] - (ptSize*0.5), ptSize, ptSize) 
                    dt.fill(0)
                    # Draw an "X" over each BCP
                    if not bPoint.bcpIn == (0, 0):
                        dt.oval(inLoc[0] - (ptSize*0.5), inLoc[1] - (ptSize*0.5), ptSize, ptSize) 
                        #dt.line((inLoc[0]-(ptSize*0.5), inLoc[1]-(ptSize*0.5)), (inLoc[0]+(ptSize*0.5), inLoc[1]+(ptSize*0.5)))
                        #dt.line((inLoc[0]+(ptSize*0.5), inLoc[1]-(ptSize*0.5)), (inLoc[0]-(ptSize*0.5), inLoc[1]+(ptSize*0.5)))
                    if not bPoint.bcpOut == (0, 0):
                        dt.oval(outLoc[0] - (ptSize*0.5), outLoc[1] - (ptSize*0.5), ptSize, ptSize) 
                        #dt.line((outLoc[0]-(ptSize*0.5), outLoc[1]-(ptSize*0.5)), (outLoc[0]+(ptSize*0.5), outLoc[1]+(ptSize*0.5)))
                        #dt.line((outLoc[0]+(ptSize*0.5), outLoc[1]-(ptSize*0.5)), (outLoc[0]-(ptSize*0.5), outLoc[1]+(ptSize*0.5)))

            dt.restore()
        
        
    def drawPreview(self, info):
        # Draw a filled in version of the interpolated glyph
        scale = info["scale"]
        if self.interpolatedGlyph:
            pen = CocoaPen(None)
            self.interpolatedGlyph.draw(pen)
            dt.fill(r=0, g=0, b=0, a=0.6)
            dt.stroke(r=None, g=None, b=None, a=1)
            dt.save()
            dt.translate(self.currentGlyph.width)
            dt.drawPath(pen.path)
            dt.restore()
            


InterpolationPreviewWindow()