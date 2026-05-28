# Drive ZAP Through Its API

We will run OWASP ZAP in daemon mode and control it through the ZAP API instead of invoking `zap-baseline.py` or `zap-full-scan.py` as one-shot subprocesses. The API path is more work, but it supports live progress, repeated scans, partial alert collection, and agent triage over discovered output; those capabilities fit a reviewer workbench better than waiting for a script to finish and parsing a static report.
