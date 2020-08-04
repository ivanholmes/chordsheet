# -*- mode: python ; coding: utf-8 -*-

# Nasty hack to get the version number included automatically
with open('_version.py', 'r') as versinfo:
   exec(versinfo.read())

block_cipher = None

a = Analysis(['/Users/ivan/Code/chordsheet/gui.py'],
             pathex=['/Users/ivan/Code/chordsheet'],
             binaries=[],
             datas=[
                ('fonts', 'fonts'),
                ('ui', 'ui')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=appName,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name=exe.name + '.app',
             icon='ui/icon.icns',
             bundle_identifier="uk.co.ivanholmes.chordsheet",
             info_plist={
                    'CFBundleShortVersionString': version,
                    'NSPrincipalClass': 'NSApplication',
                    'NSHighResolutionCapable': 'True',
                    'NSHumanReadableCopyright': "© Ivan Holmes, 2020. Some rights reserved."
                    }
            )
