
---

# AI Forensics – CAT-Net Integrated Flask Application

This repository contains a Flask-based web application that integrates the CAT-Net model for tampered image detection. Follow the steps below to correctly configure the environment, place required files, and run the application.

---

## 1. Requirements

* Python 3.9+
* Conda (recommended, particularly for installing `jpegio`)
* Model Weights:

  * `CAT_full_v2.pth.tar`

---

## 2. File Placement

Ensure all required files and folders are placed in the correct locations:

| File/Folder               | Destination               |
| ------------------------- | ------------------------- |
| `CAT_full_v2.pth.tar`     | `app/catnet_core/`        |
| `jpegio/` (source folder) | `app/catnet_core/jpegio/` |
| `lib/`, `Splicing/`       | `app/catnet_core/`        |

The directory structure should look like this:

```
app/
 └── catnet_core/
      ├── CAT_full_v2.pth.tar
      ├── jpegio/
      ├── lib/
      └── Splicing/
```

---

## 3. Installation and Environment Setup

Use Conda for a stable and compatible environment, especially for the `jpegio` dependency.

### 1. Create and Activate Conda Environment

```powershell
conda create -n catnet_env python=3.11
conda activate catnet_env
```

### 2. Install Required Python Packages

```powershell
pip install -r requirements.txt
```

### 3. Install jpegio (Important)

`jpegio` does not reliably install via pip on Windows.

```powershell
pip install -e .\jpegio
python setup.py install
```

---

## 4. Running the Application

### A. Set Environment Variables

These must be set for the Flask application to run:

```powershell
$env:FLASK_ENV="development"
$env:SECRET_KEY="**"
```

### B. Start the Flask Server

```powershell
python run.py
```

Once the server is running, open your browser and go to:

```
http://127.0.0.1:5000
```

---

## 5. Notes

* Ensure that model weights and folder structure are correctly placed before running.
* If `jpegio` causes installation issues, verify that Conda is properly configured on your system.

