import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock

from web_ui import server


class FakeProcess:
    def __init__(self) -> None:
        self.stdout = io.StringIO("")
        self.stderr = io.StringIO("")
        self.stdin = io.StringIO()
        self._poll_count = 0
        self.returncode = 0

    def poll(self) -> Optional[int]:
        if self._poll_count == 0:
            self._poll_count += 1
            return None
        return self.returncode

    def wait(self) -> int:
        return self.returncode


class WebUiExecutionTests(unittest.TestCase):
    def test_execute_command_streams_initial_message(self) -> None:
        payload = {"path": "/data/sample.mkv", "args": "--flag value", "session_id": "abc"}

        with server.app.test_request_context(
            "/api/execute", method="POST", json=payload
        ):
            with (
                mock.patch.object(server, "_verify_csrf_header", return_value=True),
                mock.patch.object(server, "_resolve_user_path", return_value="/data/sample.mkv"),
                mock.patch.object(server, "_assert_safe_resolved_path"),
                mock.patch.dict(os.environ, {"UA_WEBUI_USE_SUBPROCESS": "1"}),
                mock.patch.object(server.subprocess, "Popen", return_value=FakeProcess()),
            ):
                response = server.execute_command()
                chunks = "".join(
                    chunk.decode() if isinstance(chunk, bytes) else chunk
                    for chunk in response.response
                )

        self.assertIn("Executing:", chunks)
        self.assertIn("upload.py", chunks)

    def test_send_input_writes_to_process_stdin(self) -> None:
        process = FakeProcess()
        server.active_processes["sess"] = {"process": process}

        with server.app.test_request_context(
            "/api/input", method="POST", json={"session_id": "sess", "input": "y"}
        ):
            with mock.patch.object(server, "_is_authenticated", return_value=True):
                response = server.send_input()

        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("y\n", process.stdin.getvalue())


@unittest.skipIf(os.name == "nt", "Docker entrypoint tests require bash and Unix paths")
class DockerEntrypointTests(unittest.TestCase):
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
