from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[],
                    excludes=[],
                    include_files=['icon.png', 'config.cfg', 'cpyHook.py'],
                    )

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('cognitiveload.py', base=base)
]

setup(name='cog_app',
      version = '0.1.1',
      description = '',
      options = dict(build_exe = buildOptions),
      executables = executables)
