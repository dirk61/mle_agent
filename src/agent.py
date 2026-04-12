import base64
import io
import tarfile
from pathlib import Path
from uuid import uuid4

import pandas as pd
from a2a.server.tasks import TaskUpdater
from a2a.types import FilePart, FileWithBytes, Message, Part, Role, TaskState, TextPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger

SUBMISSION_DIR = Path("/tmp/mle_agent_submissions")


class Agent:
    def __init__(self):
        self.messenger = Messenger()
        # Initialize other state here

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Implement your agent logic here.

        Args:
            message: The incoming message
            updater: Report progress (update_status) and results (add_artifact)

        Use self.messenger.talk_to_agent(message, url) to call other agents.
        """
        # ── Detect if this is a validation reply from the green agent ──────────
        # The green agent sends back a plain-text Message (no FilePart) after we
        # request validation. We just log it and return — the executor will have
        # already stored this text so the outer run() that sent the validate
        # status update can read it via the next incoming message.
        has_file = any(isinstance(p.root, FilePart) for p in message.parts)
        if not has_file:
            validation_text = get_message_text(message)
            print(f"[VALIDATION RESULT] {validation_text}", flush=True)
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"Validation response received: {validation_text}")
            )
            return

        # ── Step 1: Extract competition.tar.gz ─────────────────────────────────
        await updater.update_status(
            TaskState.working, new_agent_text_message("Extracting competition data...")
        )

        tar_bytes = None
        for part in message.parts:
            if isinstance(part.root, FilePart):
                file_data = part.root.file
                if isinstance(file_data, FileWithBytes):
                    tar_bytes = base64.b64decode(file_data.bytes)
                    break

        if tar_bytes is None:
            await updater.update_status(
                TaskState.failed, new_agent_text_message("No competition tar file found in message.")
            )
            return

        # ── Step 2: Unpack tar and read test.csv ───────────────────────────────
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
            test_member = next(
                (m for m in tar.getmembers() if m.name.endswith("test.csv")), None
            )
            if test_member is None:
                await updater.update_status(
                    TaskState.failed, new_agent_text_message("test.csv not found in competition tar.")
                )
                return
            test_csv_bytes = tar.extractfile(test_member).read()

        test_df = pd.read_csv(io.BytesIO(test_csv_bytes))

        # ── Step 3: Build dummy submission (all-False) ─────────────────────────
        # Format: PassengerId (str), Transported (bool as Python bool → "False"/"True")
        submission = pd.DataFrame({
            "PassengerId": test_df["PassengerId"],
            "Transported": False,
        })

        # ── Step 4: Save submission.csv locally ───────────────────────────────
        SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
        local_path = SUBMISSION_DIR / "submission.csv"
        submission.to_csv(local_path, index=False)
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"Saved submission locally to {local_path} ({len(submission)} rows)")
        )

        # ── Step 5: Validate submission format with the green agent ────────────
        csv_bytes = local_path.read_bytes()
        await updater.update_status(
            TaskState.working,
            message=Message(
                kind="message",
                role=Role.agent,
                parts=[
                    Part(root=TextPart(text="validate")),
                    Part(root=FilePart(
                        file=FileWithBytes(
                            bytes=base64.b64encode(csv_bytes).decode("ascii"),
                            name="submission.csv",
                            mime_type="text/csv",
                        )
                    )),
                ],
                message_id=uuid4().hex,
            )
        )
        # Green agent will reply with a new Message on the same context_id,
        # which re-enters run() above and logs the validation result text.

        # ── Step 6: Submit final artifact ──────────────────────────────────────
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"Submitting final submission ({len(submission)} rows)...")
        )
        await updater.add_artifact(
            parts=[Part(root=FilePart(
                file=FileWithBytes(
                    bytes=base64.b64encode(csv_bytes).decode("ascii"),
                    name="submission.csv",
                    mime_type="text/csv",
                )
            ))],
            name="submission",
        )
