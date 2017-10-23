from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[],
                    excludes=[],
                    include_files=['icon.png', 'lab_config.cfg'],
                    )

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('lab_test.py', base=base)
]

setup(name='lab_cog_app',
      version = '0.5.3',
      description = '',
      options = dict(build_exe = buildOptions),
      executables = executables)
