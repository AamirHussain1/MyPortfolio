import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import naukri_task


class NaukriTaskRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.instance_directory = self.root / "instance"
        self.updater = self.root / "update_naukri.py"
        self.updater.write_text("# mocked updater entry point\n", encoding="utf-8")
        self.resume = self.root / "Aamir_Hussain_Resume.pdf"
        self.resume.write_bytes(b"%PDF-current portfolio resume")
        self.settings = {
            "PROJECT_ROOT": naukri_task.PROJECT_ROOT,
            "INSTANCE_DIR": naukri_task.INSTANCE_DIR,
            "STATE_PATH": naukri_task.STATE_PATH,
            "LOCK_PATH": naukri_task.LOCK_PATH,
            "LOG_PATH": naukri_task.LOG_PATH,
            "UPDATER_PATH": naukri_task.UPDATER_PATH,
            "AUTOMATION_PYTHON": naukri_task.AUTOMATION_PYTHON,
            "ORIGINAL_RESUME_PATH": naukri_task.ORIGINAL_RESUME_PATH,
            "UPDATED_RESUME_PATH": naukri_task.UPDATED_RESUME_PATH,
        }
        naukri_task.INSTANCE_DIR = self.instance_directory
        naukri_task.STATE_PATH = self.instance_directory / "naukri_status.json"
        naukri_task.LOCK_PATH = self.instance_directory / "naukri_job.lock"
        naukri_task.LOG_PATH = self.instance_directory / "naukri_job.log"
        naukri_task.UPDATER_PATH = self.updater
        naukri_task.AUTOMATION_PYTHON = Path(sys.executable)
        naukri_task.ORIGINAL_RESUME_PATH = self.resume
        naukri_task.UPDATED_RESUME_PATH = self.instance_directory / "resume.pdf"

    def tearDown(self):
        for name, value in self.settings.items():
            setattr(naukri_task, name, value)
        self.temp_directory.cleanup()

    @patch("naukri_task.subprocess.run")
    def test_runner_scopes_existing_script_to_aamir_and_active_resume(self, run_updater):
        run_updater.return_value = subprocess.CompletedProcess([], 0)

        result = naukri_task.main()

        self.assertEqual(result, 0)
        command = run_updater.call_args.args[0]
        environment = run_updater.call_args.kwargs["env"]
        self.assertEqual(command[1], str(self.updater))
        self.assertEqual(environment["PORTFOLIO_NAUKRI_AAMIR_ONLY"], "1")
        self.assertEqual(
            environment["PORTFOLIO_NAUKRI_RESUME_PATH"],
            str(self.resume),
        )
        status = json.loads(naukri_task.STATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "completed")
        self.assertFalse(naukri_task.LOCK_PATH.exists())

    @patch("naukri_task.subprocess.run")
    def test_runner_uses_uploaded_resume_and_records_failure(self, run_updater):
        naukri_task.UPDATED_RESUME_PATH.parent.mkdir(parents=True)
        naukri_task.UPDATED_RESUME_PATH.write_bytes(b"%PDF-uploaded")
        run_updater.return_value = subprocess.CompletedProcess([], 1)

        result = naukri_task.main()

        self.assertEqual(result, 1)
        self.assertEqual(
            run_updater.call_args.kwargs["env"]["PORTFOLIO_NAUKRI_RESUME_PATH"],
            str(naukri_task.UPDATED_RESUME_PATH),
        )
        status = json.loads(naukri_task.STATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["exit_code"], 1)

    def test_runner_does_not_start_a_second_concurrent_update(self):
        naukri_task.INSTANCE_DIR.mkdir(parents=True)
        naukri_task.LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")

        result = naukri_task.main()

        self.assertEqual(result, 3)
        self.assertTrue(naukri_task.LOCK_PATH.exists())


if __name__ == "__main__":
    unittest.main()
