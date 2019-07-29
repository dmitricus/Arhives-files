from cx_Freeze import setup, Executable


executables = [Executable('main.py',
                          targetName='arhive_pack.exe',
                          base='Win32GUI',
                          icon='main_icon.ico')]

zip_include_packages = ['PyQt5', 'application', 'threading', 'time', 'Queue', 'Empty', 'Full', 'sys', 'os', 'PIL']

include_files = ['7z', 'img', 'application.py', 'Arhives_Queue.py']

options = {
    'build_exe': {
        'include_msvcr': True,
        'zip_include_packages': zip_include_packages,
        'build_exe': 'build_windows',
    }
}

setup(
    name = "zipPack",
    version = "0.0004",
    description = "zipPack",
    executables=executables,
    options=options
)