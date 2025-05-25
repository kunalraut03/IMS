@echo off
echo Starting Inventory Management System (IMS)...

REM Check if IMS application files are present (folder installation check)
echo Checking for IMS installation...
if not exist "main.py" (
    echo ERROR: main.py not found. Please ensure IMS files are in the current directory.
    pause
    exit /b 1
)

if not exist "capture_images.py" (
    echo ERROR: capture_images.py not found. Please ensure all IMS files are in the current directory.
    pause
    exit /b 1
)

if not exist "train.py" (
    echo ERROR: train.py not found. Please ensure all IMS files are in the current directory.
    pause
    exit /b 1
)

echo IMS files found! Checking environment...

REM Check if conda is available
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Conda is not found in PATH. Trying to run with system Python...
    echo.
    echo ========================================
    echo   Starting IMS with System Python...
    echo ========================================
    python --version
    echo Launching main application window...
    python main.py
    if %errorlevel% neq 0 (
        echo.
        echo Application failed with system Python. Please install Anaconda/Miniconda for optimal performance.
        pause
    )
    goto :end
)

REM Check if imsv3 environment exists
conda info --envs | findstr "imsv3" >nul
set ENV_EXISTS=%errorlevel%

REM If environment exists and working, go directly to main window
if %ENV_EXISTS% equ 0 (
    echo imsv3 environment found! Testing environment...
    call conda activate imsv3
    
    REM Quick test if environment is working
    python -c "import tensorflow, cv2, numpy; print('Environment OK')" >nul 2>nul
    if %errorlevel% equ 0 (
        echo Environment is working! Launching application...
        goto :start_app
    ) else (
        echo Environment has issues. Offering reinstall option...
    )
)

REM Give user setup options only if environment doesn't exist or has issues
echo.
echo ========================================
echo   IMS Environment Setup Options
echo ========================================
echo.
if %ENV_EXISTS% equ 0 (
    echo imsv3 environment detected but has issues!
    echo.
    echo 1. Try to fix environment (Reinstall packages)
    echo 2. Reinstall environment (Fresh setup)
    echo 3. Use system Python (May have limited functionality)
    echo 4. Exit
    echo.
    set /p choice="Enter your choice (1-4): "
) else (
    echo No imsv3 environment found.
    echo.
    echo 1. Create new environment (Recommended for first run)
    echo 2. Use system Python (May have limited functionality)
    echo 3. Exit
    echo.
    set /p choice="Enter your choice (1-3): "
)

REM Handle user choice
if %ENV_EXISTS% equ 0 (
    if "%choice%"=="1" goto :fix_environment
    if "%choice%"=="2" goto :fresh_install
    if "%choice%"=="3" goto :use_system_python
    if "%choice%"=="4" goto :exit
    echo Invalid choice. Trying to fix environment...
    goto :fix_environment
) else (
    if "%choice%"=="1" goto :fresh_install
    if "%choice%"=="2" goto :use_system_python
    if "%choice%"=="3" goto :exit
    echo Invalid choice. Creating new environment...
    goto :fresh_install
)

:fix_environment
echo.
echo ========================================
echo   Fixing existing environment...
echo ========================================

call conda activate imsv3

echo Updating packages...
pip install --upgrade tensorflow==2.10 opencv-python keras pillow numpy matplotlib scikit-learn
if %errorlevel% neq 0 (
    echo WARNING: Some packages may not have updated correctly
)

goto :start_app

:fresh_install
echo.
echo ========================================
echo   Setting up fresh environment...
echo ========================================

REM Remove existing environment if it exists
if %ENV_EXISTS% equ 0 (
    echo Removing existing imsv3 environment...
    conda remove -n imsv3 --all -y
)

echo Creating conda environment 'imsv3' with Python 3.10...
conda create -n imsv3 python=3.10 -y
if %errorlevel% neq 0 (
    echo ERROR: Failed to create conda environment 'imsv3'
    pause
    exit /b 1
)

echo Activating imsv3 environment...
call conda activate imsv3

echo Installing CUDA toolkit and cuDNN from conda-forge...
conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0 -y
if %errorlevel% neq 0 (
    echo WARNING: Failed to install CUDA toolkit or cuDNN
)

echo Installing CUDA NVCC compiler...
conda install -c nvidia cuda-nvcc -y
if %errorlevel% neq 0 (
    echo WARNING: Failed to install CUDA NVCC
)

echo Installing TensorFlow 2.10...
pip install tensorflow==2.10
if %errorlevel% neq 0 (
    echo WARNING: Failed to install TensorFlow 2.10
)

echo Installing other required packages...
pip install opencv-python keras pillow numpy matplotlib scikit-learn
if %errorlevel% neq 0 (
    echo WARNING: Some packages may not have installed correctly
)

echo Environment setup complete!
goto :start_app

:use_system_python
echo.
echo ========================================
echo   Using System Python...
echo ========================================

python --version
echo WARNING: Using system Python may result in limited functionality.
echo For optimal performance, consider setting up the conda environment.
echo.

:start_app
echo.
echo ========================================
echo   Starting IMS Application...
echo ========================================

REM Verify Python environment
if defined CONDA_PREFIX (
    echo Using Python from: %CONDA_PREFIX%
    set PYTHON_EXECUTABLE=%CONDA_PREFIX%\python.exe
) else (
    echo Using system Python
    where python
)

python --version

REM Check CUDA availability if using conda environment
if defined CONDA_PREFIX (
    echo Checking CUDA availability...
    python -c "import tensorflow as tf; print('CUDA Build:', tf.test.is_built_with_cuda()); print('GPU Devices:', len(tf.config.list_physical_devices('GPU')))" 2>nul
)

echo.
echo Launching main application window...
python main.py

REM Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
goto :end

:exit
echo.
echo Exiting...
goto :end

:end
