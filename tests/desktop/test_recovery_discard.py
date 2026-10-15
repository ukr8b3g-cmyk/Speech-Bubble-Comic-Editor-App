"""Discarding a draft must not revive older recovery generations."""
import tempfile
import unittest
from pathlib import Path
from desktop_app.recovery_store import RecoveryStore


def layout():
    workspaces = {}
    for name, width, height in [("single", 1024, 1024), ("comic", 720, 2200), ("comic_layout", 2480, 3508)]:
        workspaces[name] = {"canvas": {"width": width, "height": height}, "elements": []}
    return {"format": "speech-bubble-editor-layout", "version": 5,
            "active_workspace": "single", "workspaces": workspaces}


class RecoveryDiscardTests(unittest.TestCase):
    def test_discard_suppresses_old_generations_until_next_autosave(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = RecoveryStore(Path(temporary) / "recovery")
            payload = {"layout": layout(), "images": [], "title": "draft"}
            store.save(payload, checkpoint=True)
            assert store.load().get("layout")
            assert list(store.generations.glob("*.json"))
            assert store.discard()["discarded"]
            assert store.load()["available"] is False
            assert store.status()["available"] is False
            assert list(store.generations.glob("*.json"))
            store.save(payload, checkpoint=True)
            assert store.load().get("layout")


if __name__ == "__main__":
    unittest.main()
