import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
STATE_PATH = INSTANCE_DIR / "naukri_status.json"
LOCK_PATH = INSTANCE_DIR / "naukri_job.lock"
LOG_PATH = INSTANCE_DIR / "naukri_job.log"
UPDATER_PATH = Path(r"D:\Resume\update_naukri.py")
AUTOMATION_PYTHON = Path(
    os.environ.get(
        "PORTFOLIO_NAUKRI_PYTHON",
        str(Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python314" / "python.exe"),
    )
)
ORIGINAL_RESUME_PATH = PROJECT_ROOT / "static" / "resume" / "Aamir_Hussain_Resume.pdf"
UPDATED_RESUME_PATH = INSTANCE_DIR / "resume.pdf"
RUN_TIMEOUT_SECONDS = 20 * 60


def _write_status(status):
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    os.replace(temporary_path, STATE_PATH)


def _lock_owner_is_running():
    try:
        process_id = int(LOCK_PATH.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False

    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def main():
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        lock_descriptor = os.open(
            LOCK_PATH,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError:
        if _lock_owner_is_running():
            print("A Naukri resume update is already running.", file=sys.stderr)
            return 3
        LOCK_PATH.unlink(missing_ok=True)
        return main()

    with os.fdopen(lock_descriptor, "w", encoding="utf-8") as lock_file:
        lock_file.write(str(os.getpid()))

    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_status(
        {
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "message": "Updating the Aamir Naukri profile.",
        }
    )

    active_resume = UPDATED_RESUME_PATH if UPDATED_RESUME_PATH.is_file() else ORIGINAL_RESUME_PATH
    environment = os.environ.copy()
    environment["PORTFOLIO_NAUKRI_AAMIR_ONLY"] = "1"
    environment["PORTFOLIO_NAUKRI_RESUME_PATH"] = str(active_resume)

    try:
        if not UPDATER_PATH.is_file():
            raise FileNotFoundError(f"Naukri updater not found: {UPDATER_PATH}")
        if not AUTOMATION_PYTHON.is_file():
            raise FileNotFoundError(
                "Python with Selenium is unavailable. Set PORTFOLIO_NAUKRI_PYTHON "
                "to the Python executable used by the existing updater."
            )
        if not active_resume.is_file():
            raise FileNotFoundError(f"Portfolio resume not found: {active_resume}")

        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"\n[{started_at}] Starting Aamir Naukri resume update.\n")
            log_file.flush()
            result = subprocess.run(
                [str(AUTOMATION_PYTHON), str(UPDATER_PATH)],
                cwd=UPDATER_PATH.parent,
                env=environment,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                timeout=RUN_TIMEOUT_SECONDS,
                check=False,
            )
            log_file.write(
                f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] "
                f"Updater process exited with code {result.returncode}.\n"
            )

        finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
        succeeded = result.returncode == 0
        _write_status(
            {
                "status": "completed" if succeeded else "failed",
                "started_at": started_at,
                "finished_at": finished_at,
                "message": (
                    "The Aamir updater completed. Verify the profile on Naukri."
                    if succeeded
                    else "The updater reported an error. Check the local run log."
                ),
                "exit_code": result.returncode,
            }
        )
        return result.returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
        _write_status(
            {
                "status": "failed",
                "started_at": started_at,
                "finished_at": finished_at,
                "message": f"Updater could not complete: {error}",
            }
        )
        return 1
    finally:
        LOCK_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
