# -*- mode: python -*-

block_cipher = None

# go to the folder this file is in from the command line
# then it's 'pyinstaller build.spec'


a = Analysis(['display.py'],
             pathex=[''],  # full path to display.py
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PySide','_ssl','win32','wx','pyexpat','unittest', 'matplotlib', 
			           'numpy', 'pytz', 'mpmath', '_hashlib', 'bz2', 'PyQt4.uic'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries - TOC([# (name, path, typecode)  # additional binaries to exclude
							#('msvcp90.dll', None, None), 
							#('msvcr90.dll', None, None),
							#('msvcm90.dll', None, None),
							]),
          a.zipfiles,
          a.datas,
          [],
          name='Base Converter',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='zero.ico')
