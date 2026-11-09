"""Exercise release selection and the workflow boundaries enforcing it."""

import unittest
import tempfile
from pathlib import Path

import yaml

from release_policy import deploy_target
from release_artifact import release_manifest


class ReleasePolicyTests(unittest.TestCase):
    def test_manifest_changes_with_the_actual_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "index.html"
            page.write_text("first", encoding="utf-8")
            args = {"revision": "a" * 40, "ref": "refs/heads/main", "run_id": "42"}
            original = release_manifest(root, **args)
            (root / "release.json").write_text("previous manifest", encoding="utf-8")
            self.assertEqual(release_manifest(root, **args), original)
            page.write_text("changed", encoding="utf-8")
            self.assertNotEqual(release_manifest(root, **args)["files"], original["files"])
            self.assertEqual(original["revision"], args["revision"])
            with self.assertRaises(ValueError):
                release_manifest(root, **{**args, "revision": "main"})
    def test_only_main_push_and_explicit_main_release_publish(self):
        self.assertEqual(deploy_target("push", "refs/heads/main"), "production")
        self.assertEqual(deploy_target("workflow_dispatch", "refs/heads/main", "production"), "production")
        for event in ("push", "pull_request", "pull_request_target", "workflow_dispatch"):
            for ref in ("refs/heads/uat", "refs/heads/feature", "refs/pull/42/merge", "refs/tags/main"):
                with self.subTest(event=event, ref=ref):
                    self.assertEqual(deploy_target(event, ref), "none")
        self.assertEqual(deploy_target("pull_request", "refs/heads/main"), "none")
        self.assertEqual(deploy_target("workflow_dispatch", "refs/heads/main"), "none")

    def test_manual_release_cannot_bypass_branch_or_restore_uat_destination(self):
        for ref in ("refs/heads/uat", "refs/heads/feature", "refs/tags/main", ""):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                deploy_target("workflow_dispatch", ref, "production")
        for target in ("uat", "", "unexpected"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                deploy_target("workflow_dispatch", "refs/heads/main", target)

    def test_pages_boundary_and_serialization(self):
        path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"
        workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertNotIn("pages", workflow["permissions"])
        self.assertNotIn("id-token", workflow["permissions"])
        self.assertNotIn("concurrency", workflow)  # New builds cannot cancel an active deployment.
        deploy = workflow["jobs"]["deploy"]
        self.assertEqual(deploy["environment"]["name"], "github-pages")
        self.assertIn("github.ref == 'refs/heads/main'", deploy["if"])
        meta = next(s for s in workflow["jobs"]["lint-build"]["steps"] if s.get("name") == "Resolve deploy target")
        self.assertIn("github.event.inputs.deploy_target", meta["env"]["DEPLOY_TARGET"])
        self.assertEqual(deploy["concurrency"], {"group": "github-pages", "cancel-in-progress": "false"})
        self.assertEqual(deploy["permissions"]["pages"], "write")
        steps = deploy["steps"]
        self.assertIn("data.object.sha !== context.sha", steps[0]["with"]["script"])
        self.assertIn("ref: 'heads/main'", steps[0]["with"]["script"])
        self.assertEqual(steps[-1]["uses"], "actions/deploy-pages@v4")
        for job_id, job in workflow["jobs"].items():
            if job_id != "deploy":
                self.assertNotIn("pages", job.get("permissions", {}))
                self.assertFalse(any(step.get("uses", "").startswith("actions/deploy-pages@") for step in job["steps"]))
        build_steps = workflow["jobs"]["lint-build"]["steps"]
        manifest_step = next(i for i, s in enumerate(build_steps) if s.get("name") == "Record release artifact")
        for i, step in enumerate(build_steps):
            if step.get("uses", "").startswith(("actions/upload-artifact@", "actions/upload-pages-artifact@")) and step.get("name") != "Upload Playwright report":
                self.assertGreater(i, manifest_step)
        build = next(s for s in build_steps if s.get("name") == "Build (GitHub Pages base path)")
        self.assertEqual(build["env"]["SITE_UAT_BUILD"], "${{ steps.meta.outputs.should_deploy != 'true' && '1' || '' }}")


if __name__ == "__main__":
    unittest.main()
