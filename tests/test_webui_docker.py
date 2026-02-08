import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from web_ui import server


class FakeProcess:
    def __init__(self) -> None:
        self.stdout = io.StringIO("")
        self.stderr = io.StringIO("")
        self.stdin = io.StringIO()
        self._poll_count = 0
        self.returncode = 0

    def poll(self) -> int | None:
        if self._poll_count == 0:
            self._poll_count += 1
            return None
        return self.returncode

    def wait(self) -> int:
        return self.returncode


class WebUiExecutionTests(unittest.TestCase):
    def test_execute_command_streams_initial_message(self) -> None:
        payload = {"path": "/data/sample.mkv", "args": "--flag value", "session_id": "abc"}

        with (
            mock.patch.object(server, "_resolve_user_path", return_value="/data/sample.mkv"),
            mock.patch.object(server.subprocess, "Popen", return_value=FakeProcess()),
        ):
            server.request.json = payload
            server.request.method = "POST"
            server.request.path = "/api/execute"
            response = server.execute_command()
            chunks = "".join(response.response)

        self.assertIn("Executing:", chunks)
        self.assertIn("upload.py", chunks)

    def test_send_input_writes_to_process_stdin(self) -> None:
        process = FakeProcess()
        server.active_processes["sess"] = {"process": process}

        server.request.json = {"session_id": "sess", "input": "y"}
        response = server.send_input()

        self.assertEqual(response["json"]["success"], True)
        self.assertIn("y\n", process.stdin.getvalue())


class DockerEntrypointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.venv_path = Path("/venv/bin")
        self.venv_path.mkdir(parents=True, exist_ok=True)
        (self.venv_path / "activate").write_text("true\n", encoding="utf-8")

    def test_entrypoint_defaults_to_upload_py(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            python_stub = bin_dir / "python"
            python_stub.write_text('#!/bin/sh\necho "$0 $@"\n', encoding="utf-8")
            python_stub.chmod(0o755)
            (temp_path / "upload.py").write_text("print('stub')\n", encoding="utf-8")

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["ENABLE_WEB_UI"] = "false"
            script_path = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"

            result = subprocess.run(
                ["bash", str(script_path)],
                cwd=str(temp_path),
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("upload.py", result.stdout)

    def test_entrypoint_wraps_non_executable_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            python_stub = bin_dir / "python"
            python_stub.write_text('#!/bin/sh\necho "$0 $@"\n', encoding="utf-8")
            python_stub.chmod(0o755)
            (temp_path / "upload.py").write_text("print('stub')\n", encoding="utf-8")

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["ENABLE_WEB_UI"] = "false"
            script_path = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"

            result = subprocess.run(
                ["bash", str(script_path), "not-a-command", "--flag"],
                cwd=str(temp_path),
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("upload.py not-a-command --flag", result.stdout)


if __name__ == "__main__":
    unittest.main()
