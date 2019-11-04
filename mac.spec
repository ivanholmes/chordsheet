# -*- mode: python ; coding: utf-8 -*-

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
          name='Chordsheet',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='Chordsheet.app',
             icon='ui/icon.icns',
             bundle_identifier=None,
             info_plist={
                    'NSPrincipalClass': 'NSApplication',
                    'NSHighResolutionCapable': 'True'
                    }
            )
