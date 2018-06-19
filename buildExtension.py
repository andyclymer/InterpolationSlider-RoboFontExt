from __future__ import absolute_import
from __future__ import print_function
import os
from mojo.extensions import ExtensionBundle


basePath = os.path.dirname(__file__)
extensionPath = os.path.join(basePath, "InterpolationSlider.roboFontExt")
libPath = os.path.join(basePath, "lib")
htmlPath = os.path.join(basePath, "html")
resourcesPath = os.path.join(basePath, "resources")

B = ExtensionBundle()

B.name = "Interpolation Slider"
B.version = "1.0"
B.mainScript = "InterpolationSlider.py"

B.developer = "Andy Clymer"
B.developerURL = 'http://www.andyclymer.com/'

B.launchAtStartUp = False
B.addToMenu = [{"path" : "InterpolationSlider.py", "preferredName" : "Interpolation Slider...", "shortKey" : ""}]
B.requiresVersionMajor = '1'
B.requiresVersionMinor = '5'
B.infoDictionary["html"] = True

B.save(extensionPath, libPath=libPath, htmlPath=htmlPath, resourcesPath=resourcesPath, pycOnly=False)

print("Done")