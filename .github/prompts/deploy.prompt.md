---
description: "Deploy all pending changes to the Jetson production server"
agent: "agent"
argument-hint: "Brief description of what changed"
---

Deploy the current changes to the Jetson Orin Nano production server. Commit all staged changes, push to GitHub, pull on the Jetson, restart the work-notes-web service, and verify the app is responding with HTTP 200.
