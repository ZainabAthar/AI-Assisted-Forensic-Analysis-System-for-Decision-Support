This guide details the steps to set up and run the Flask application integrating the CAT-Net model.

# 1. Requirements

Python 3.9+

Conda: Recommended for installing jpegio.

Model Weights: CAT_full_v2.pth.tar.

# 2. File Placement

Ensure your model weights and core dependencies are correctly located:

File/Folder	Destination
CAT_full_v2.pth.tar	app/catnet_core/
jpegio/ source	app/catnet_core/jpegio/
lib/, Splicing/	app/catnet_core/

# 3. Installation & Environment

Use Conda to ensure stability, especially for the critical jpegio dependency.

code
Powershell
download
content_copy
expand_less

# 1. Create and activate environment
conda create -n catnet_env python=3.11
conda activate catnet_env

# 2. Install all core dependencies
pip install -r requirements.txt

# 3. Install the complex dependency
conda install -c conda-forge jpegio

# 4. Running the Application
Set required environment variables and launch the Flask server.

code
Powershell
download
content_copy
expand_less
# A. Set Variables (Required in session)
$env:FLASK_ENV="development"
$env:SECRET_KEY="your_super_secret_key_12345"

# B. Launch Server
python run.py

 
