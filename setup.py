import PyInstaller.__main__
import os
import sys
import shutil

def create_executable():
    """Create executable using PyInstaller"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    
    # PyInstaller arguments
    args = [
        '--name=IMS',
        '--onefile',
        '--windowed',
        '--icon=icon.ico' if os.path.exists(os.path.join(script_dir, 'icon.ico')) else '',
        '--add-data=*.py;.',
        '--hidden-import=PIL',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=tensorflow',
        '--hidden-import=sklearn',
        main_script
    ]
    
    # Remove empty icon argument if no icon file exists
    args = [arg for arg in args if arg]
    
    print("Building executable with PyInstaller...")
    print(f"Arguments: {args}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\nExecutable created successfully!")
        print(f"Location: {os.path.join(script_dir, 'dist', 'IMS.exe')}")
        
        # Create a simple installer batch file
        create_installer_batch(script_dir)
        
    except Exception as e:
        print(f"Error creating executable: {e}")
        return False
    
    return True

def create_installer_batch(script_dir):
    """Create a simple batch file for easy installation"""
    batch_content = '''@echo off
echo Installing IMS (Inventory Management System)...
echo.

REM Create installation directory
if not exist "%USERPROFILE%\\IMS" mkdir "%USERPROFILE%\\IMS"

REM Copy all Python files
copy /Y *.py "%USERPROFILE%\\IMS\\"

REM Copy executable
copy /Y dist\\IMS.exe "%USERPROFILE%\\IMS\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\IMS.lnk'); $Shortcut.TargetPath = '%USERPROFILE%\\IMS\\IMS.exe'; $Shortcut.WorkingDirectory = '%USERPROFILE%\\IMS'; $Shortcut.Save()"

echo.
echo Installation completed!
echo You can find IMS shortcut on your desktop.
echo Installation location: %USERPROFILE%\\IMS
pause
'''
    
    batch_file = os.path.join(script_dir, "install_ims.bat")
    with open(batch_file, "w") as f:
        f.write(batch_content)
    
    print(f"Installer batch file created: {batch_file}")

def install_requirements():
    """Install required packages"""
    requirements = [
        'pyinstaller',
        'opencv-python',
        'tensorflow',
        'numpy',
        'pillow',
        'scikit-learn'
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")

if __name__ == "__main__":
    print("IMS Executable Builder")
    print("=" * 50)
    
    choice = input("Do you want to install required packages first? (y/n): ").lower()
    if choice == 'y':
        install_requirements()
    
    print("\nBuilding executable...")
    success = create_executable()
    
    if success:
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("Next steps:")
        print("1. Run 'install_ims.bat' as administrator to install IMS system-wide")
        print("2. Or run 'dist/IMS.exe' directly from this folder")
        print("=" * 50)
    else:
        print("Build failed. Please check the error messages above.")
