import _version

with open('version.rc.template', 'r') as verstf:
    verstemp = verstf.read()
    
major, minor, patch = _version.version.split(".")

verstemp = verstemp.replace("%APPNAME%", _version.appName)
verstemp = verstemp.replace("%VERSION%", _version.version)
verstemp = verstemp.replace("%MAJOR_VERSION%", major)
verstemp = verstemp.replace("%MINOR_VERSION%", minor)
verstemp = verstemp.replace("%PATCH_VERSION%", patch)

with open('version.rc', 'w') as versf:
    versf.write(verstemp)