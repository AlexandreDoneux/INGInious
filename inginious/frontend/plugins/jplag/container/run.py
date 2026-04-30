from inginious_container_api import feedback
import subprocess
import os
import zipfile


# ─── Paths ────────────────────────────────────────────────────────────────────
#
#   ZIP_PATH        : path to the input zip file containing the submissions zip (required)
#   SUBMISSIONS_DIR : path to the directory where the submissions will be extracted
#   RESULT_FILE     : path to the JPlag result file (without extension, JPlag will add .jplag)
#   BASE_CODE_DIR   : path to the directory containing the base code (optional, only if you want to use

ZIP_PATH        = "/jplag/input/submissions.zip"
SUBMISSIONS_DIR = "/jplag/submissions"
RESULT_FILE      = "/jplag/result/results.jplag"
BASE_CODE_DIR   = "/jplag/basecode"


# ─── Configuration (environment variables) ────────────────────────────────────
#
#   JAVA_JAR        : path to the jplag jar file (required)
#   JPLAG_LANGUAGE            : e.g. java, python3, cpp, typescript (default: java)
#   JPLAG_SIMILARITY_THRESHOLD: minimum similarity to store -m (default: 0.0)
#   JPLAG_SUBDIRECTORY        : scan only this subdir inside each submission (optional)

JAVA_JAR        = os.environ["JPLAG_JAR"]
LANGUAGE      = os.environ.get("JPLAG_LANGUAGE")
SIM_THRESHOLD = os.environ.get("JPLAG_SIMILARITY_THRESHOLD")


# ─── 1. Extract the submissions zip ───────────────────────────────────────────
#
# Supported zip layout:
#
# one folder per student:
#   submissions.zip
#   ├── alice/
#   │   └── Solution.java
#   ├── bob/
#   │   ├── Main.java
#   │   └── util/Helper.java
#   └── charlie/
#       └── answer.py
#

if not os.path.isfile(ZIP_PATH):
    print(f"ERROR: submissions zip not found at '{ZIP_PATH}'.")
    feedback.set_global_result("failed")
    raise SystemExit(1)

print(f"Extracting '{ZIP_PATH}' ...")
with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    zf.extractall(SUBMISSIONS_DIR)
print("Extraction complete.")


submissions = [
    d for d in os.listdir(SUBMISSIONS_DIR)
    if os.path.isdir(os.path.join(SUBMISSIONS_DIR, d)) and not d.startswith("_")
]
print(f"Found {len(submissions)} submission(s): {submissions}")

if len(submissions) < 2:
    print(f"ERROR: at least 2 submissions required, found {len(submissions)}.")
    feedback.set_global_result("failed")
    raise SystemExit(1)


# ─── 2. Build the JPlag command ────────────────────────────────────────────────

cmd = [
    "java", "-jar", JAVA_JAR,
    "--mode", "run",   # not launching the GUI viewer
    "-l", LANGUAGE,
    "-r", RESULT_FILE,
    "--overwrite",
]


if SIM_THRESHOLD:
    cmd += ["-m", SIM_THRESHOLD]
if os.path.isdir(BASE_CODE_DIR):
    cmd += ["-b", BASE_CODE_DIR]

cmd.append(SUBMISSIONS_DIR)


# ─── 3. Run JPlag ──────────────────────────────────────────────────────────────

proc = subprocess.run(cmd, capture_output=True, text=True)


print("JPlag executed successfully.")
print(f"Report written to: {RESULT_FILE }.jplag")

feedback.set_global_result("success")
