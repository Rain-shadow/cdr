# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['D:\\WorkSpace\\Python\\cdr-new\\cdr',
					 'D:\\Python\\Python37-32\\Lib\\site-packages',
					 'D:\\Python\\Python37-32\\Lib\\site-packages\\requests'],
             binaries=None,
             datas=None,
             hiddenimports=['requests', 'qrcode', 'Image', 'urllib3',
							'cdr.config',
							'cdr.eprogress.eprogress',
							'cdr.test', 'cdr.test.cdr_task',
							'cdr.thread',
							'cdr.utils', 'cdr.utils.adapt',
							'cdr.request', 'cdr.request.network_error'],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='词达人',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
		  icon='favicon.ico',
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='main')
