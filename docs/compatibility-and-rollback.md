# v1.0.1 hardening notes

The frozen v1.0 directory and public repository are immutable inputs. v1.0.1 writes only its own state/log directory and host-local service registration.

Mac: install the plist after substituting paths, then `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.gpt.multibody.heartbeat.plist`. Roll back with `launchctl bootout gui/$UID/...` and remove only the v1.0.1 plist/state directory.

Windows: run `Install-HeartbeatTask.ps1 -Action DryRun`, then `Install` or `Repair`; rollback is `Disable` or `Uninstall`. The task runs as SYSTEM with limited run level and only writes its state/log directory. It does not call or alter inference, CUDA, NVIDIA, Ollama, Tailscale, RDP, SSH, or user project services.

Health evaluation preserves v1.0: age <= 45s is ONLINE/BUSY, <= 90s is STALE, then ORPHANED. Automatic RETRY is forbidden unless the lease has `side_effect_state=NONE` and idempotency is confirmed by the control plane.
