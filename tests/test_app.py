import json
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app import app


class PortfolioPageTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        app.config["ADMIN_PASSWORD"] = "test-only-password"
        self.original_resume_upload_setting = app.config["ENABLE_RESUME_UPLOADS"]
        self.original_naukri_setting = app.config["ENABLE_NAUKRI_AUTOMATION"]
        self.original_project_management_setting = app.config["ENABLE_PROJECT_MANAGEMENT"]
        app.config["ENABLE_RESUME_UPLOADS"] = True
        app.config["ENABLE_NAUKRI_AUTOMATION"] = True
        app.config["ENABLE_PROJECT_MANAGEMENT"] = True
        self.resume_directory = TemporaryDirectory()
        self.original_updated_resume_path = app.config["UPDATED_RESUME_PATH"]
        self.original_admin_password_path = app.config["ADMIN_PASSWORD_PATH"]
        self.original_naukri_status_path = app.config["NAUKRI_STATUS_PATH"]
        self.original_added_projects_path = app.config["ADDED_PROJECTS_PATH"]
        app.config["UPDATED_RESUME_PATH"] = Path(self.resume_directory.name) / "resume.pdf"
        app.config["ADMIN_PASSWORD_PATH"] = Path(self.resume_directory.name) / "admin-password.txt"
        app.config["NAUKRI_STATUS_PATH"] = Path(self.resume_directory.name) / "naukri-status.json"
        app.config["ADDED_PROJECTS_PATH"] = Path(self.resume_directory.name) / "projects.json"
        self.client = app.test_client()

    def tearDown(self):
        app.config.pop("ADMIN_PASSWORD", None)
        app.config["ENABLE_RESUME_UPLOADS"] = self.original_resume_upload_setting
        app.config["ENABLE_NAUKRI_AUTOMATION"] = self.original_naukri_setting
        app.config["ENABLE_PROJECT_MANAGEMENT"] = self.original_project_management_setting
        app.config["UPDATED_RESUME_PATH"] = self.original_updated_resume_path
        app.config["ADMIN_PASSWORD_PATH"] = self.original_admin_password_path
        app.config["NAUKRI_STATUS_PATH"] = self.original_naukri_status_path
        app.config["ADDED_PROJECTS_PATH"] = self.original_added_projects_path
        self.resume_directory.cleanup()

    def test_home_page_renders_portfolio_sections(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Aamir Hussain", page)
        self.assertIn("Silicon Automation &amp; Validation Engineer", page)
        self.assertIn("300+ test cases", page)
        self.assertIn("Microsoft Maia 200 / 300", page)
        self.assertIn("Intel Xeon server platforms", page)
        self.assertIn("Jammu University", page)
        self.assertIn("Career highlights", page)
        self.assertIn("validation-title", page)
        self.assertIn("1S–8S", page)
        self.assertIn("PCIe Gen4 / Gen5 / Gen6", page)
        self.assertIn("Memory &amp; training", page)
        self.assertIn("toolkit.", page)
        self.assertIn("aamirbhet@gmail.com", page)
        self.assertIn("/resume", page)
        self.assertIn("Naukri Resume Updater", page)
        self.assertIn('href="https://www.linkedin.com/in/aamirhussainbhat"', page)
        self.assertIn('id="lifecycle"', page)
        self.assertIn('id="lab"', page)
        self.assertIn("PCIe Explorer", page)
        self.assertIn("Memory Explorer", page)
        self.assertIn("SR-IOV Explorer", page)
        self.assertIn('id="debug"', page)
        self.assertIn("JTAG, ITP, and logic analyzers", page)
        self.assertIn(">LinkedIn", page)
        self.assertNotIn("wordmark-mark", page)
        self.assertNotIn("profile-photo", page)
        self.assertNotIn("hero-art", page)
        self.assertNotIn("hello.py", page)

    def test_static_assets_are_available(self):
        for asset in (
            "/static/css/style.css",
            "/static/js/main.js",
            "/static/images/silicon-background.svg",
            "/static/images/wafer-background.svg",
        ):
            with self.subTest(asset=asset):
                response = self.client.get(asset)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_hosted_local_only_features_can_be_disabled(self):
        original_upload_setting = app.config["ENABLE_RESUME_UPLOADS"]
        original_naukri_setting = app.config["ENABLE_NAUKRI_AUTOMATION"]
        original_project_setting = app.config["ENABLE_PROJECT_MANAGEMENT"]
        app.config["ENABLE_RESUME_UPLOADS"] = False
        app.config["ENABLE_NAUKRI_AUTOMATION"] = False
        app.config["ENABLE_PROJECT_MANAGEMENT"] = False
        try:
            home_response = self.client.get("/")
            self.assertEqual(home_response.status_code, 200)
            self.assertNotIn("Naukri Resume Updater", home_response.get_data(as_text=True))
            self.assertNotIn("Update resume", home_response.get_data(as_text=True))
            self.assertEqual(self.client.get("/resume/upload").status_code, 404)
            self.assertEqual(self.client.get("/projects/manage").status_code, 404)
            self.assertEqual(self.client.get("/todos").status_code, 404)
            self.assertEqual(self.client.get("/todos/naukri").status_code, 404)
        finally:
            app.config["ENABLE_RESUME_UPLOADS"] = original_upload_setting
            app.config["ENABLE_NAUKRI_AUTOMATION"] = original_naukri_setting
            app.config["ENABLE_PROJECT_MANAGEMENT"] = original_project_setting

    def test_project_manager_requires_admin_password(self):
        response = self.client.post(
            "/projects/manage",
            data={"action": "add", "password": "incorrect"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Path(app.config["ADDED_PROJECTS_PATH"]).exists())

    def test_project_can_be_added_persisted_and_shown_on_homepage(self):
        response = self.client.post(
            "/projects/manage",
            data={
                "action": "add",
                "password": "test-only-password",
                "title": "Portfolio dashboard",
                "label": "Web application",
                "description": "A dashboard built with Flask.",
                "tags": "Python, Flask",
                "link": "https://example.com/project",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/projects/manage?added=1", response.location)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Portfolio dashboard", page)
        self.assertIn("Python", page)
        self.assertIn('href="https://example.com/project"', page)
        self.assertIn('class="project-number">03</span>', page)
        stored = Path(app.config["ADDED_PROJECTS_PATH"]).read_text(encoding="utf-8")
        self.assertIn("Portfolio dashboard", stored)

    def test_project_manager_rejects_invalid_project_link(self):
        response = self.client.post(
            "/projects/manage",
            data={
                "action": "add",
                "password": "test-only-password",
                "title": "Unsafe link",
                "label": "Web application",
                "description": "A project description.",
                "tags": "Python",
                "link": "javascript:alert(1)",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("valid HTTPS or HTTP URL", response.get_data(as_text=True))
        self.assertFalse(Path(app.config["ADDED_PROJECTS_PATH"]).exists())

    def test_added_project_can_be_removed(self):
        response = self.client.post(
            "/projects/manage",
            data={
                "action": "add",
                "password": "test-only-password",
                "title": "Temporary project",
                "label": "Test",
                "description": "A temporary entry.",
                "tags": "Python",
            },
        )
        self.assertEqual(response.status_code, 302)
        projects_path = Path(app.config["ADDED_PROJECTS_PATH"])
        project = json.loads(projects_path.read_text(encoding="utf-8"))[0]
        removed = self.client.post(
            "/projects/manage",
            data={
                "action": "delete",
                "password": "test-only-password",
                "project_id": project["id"],
            },
        )

        self.assertEqual(removed.status_code, 302)
        self.assertEqual(projects_path.read_text(encoding="utf-8").strip(), "[]")

    def test_naukri_resume_updater_page_renders_update_card(self):
                response = self.client.get("/todos")

                self.assertEqual(response.status_code, 200)
                page = response.get_data(as_text=True)
                self.assertIn("Naukri Resume Updater", page)
                self.assertIn("Update my Naukri resume", page)
                self.assertIn("8:15", page)
                self.assertIn("mnjuser/homepage", page)

    def test_naukri_actions_require_the_admin_password(self):
                response = self.client.post(
                    "/todos/naukri",
                    data={"action": "run", "password": "incorrect"},
                )

                self.assertEqual(response.status_code, 403)

    @patch("app.update_naukri_schedule", return_value=(True, "Daily schedule enabled."))
    def test_authorized_naukri_schedule_can_be_enabled(self, update_schedule):
                response = self.client.post(
                    "/todos/naukri",
                    data={"action": "schedule", "password": "test-only-password"},
                )

                self.assertEqual(response.status_code, 200)
                self.assertIn("Daily schedule enabled.", response.get_data(as_text=True))
                update_schedule.assert_called_once_with(True)

    @patch("app.subprocess.Popen")
    def test_authorized_naukri_run_starts_the_portfolio_runner(self, start_process):
                response = self.client.post(
                    "/todos/naukri",
                    data={"action": "run", "password": "test-only-password"},
                )

                self.assertEqual(response.status_code, 302)
                self.assertIn("/todos/naukri?started=1", response.location)
                start_process.assert_called_once()
                self.assertIn("naukri_task.py", start_process.call_args.args[0][1])


    def test_resume_download_returns_original_pdf_as_attachment(self):
        response = self.client.get("/resume")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("Aamir_Hussain_Resume.pdf", response.headers["Content-Disposition"])
        self.assertTrue(response.data.startswith(b"%PDF-"))
        response.close()

    def test_resume_upload_requires_password_and_replaces_download(self):
        upload_path = Path(app.config["UPDATED_RESUME_PATH"])
        payload = {"resume": (BytesIO(b"%PDF-updated resume"), "updated.pdf")}

        denied = self.client.post(
            "/resume/upload",
            data={**payload, "password": "incorrect"},
            content_type="multipart/form-data",
        )
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(upload_path.exists())

        accepted = self.client.post(
            "/resume/upload",
            data={
                "resume": (BytesIO(b"%PDF-updated resume"), "updated.pdf"),
                "password": "test-only-password",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(upload_path.read_bytes(), b"%PDF-updated resume")

        download = self.client.get("/resume")
        self.assertEqual(download.data, b"%PDF-updated resume")
        download.close()

    def test_upload_page_provisions_a_local_admin_password(self):
        app.config.pop("ADMIN_PASSWORD", None)
        try:
            with patch.dict("os.environ", {"PORTFOLIO_ADMIN_PASSWORD": ""}):
                response = self.client.get("/resume/upload")
        finally:
            app.config["ADMIN_PASSWORD"] = "test-only-password"

        password = Path(app.config["ADMIN_PASSWORD_PATH"]).read_text(encoding="utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Admin password", response.get_data(as_text=True))
        self.assertGreaterEqual(len(password), 32)

    def test_resume_upload_rejects_non_pdf_files(self):
        response = self.client.post(
            "/resume/upload",
            data={
                "resume": (BytesIO(b"not a PDF"), "notes.txt"),
                "password": "test-only-password",
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
