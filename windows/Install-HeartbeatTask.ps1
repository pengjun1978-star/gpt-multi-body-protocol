param([ValidateSet('Install','Repair','Disable','Uninstall','DryRun')][string]$Action='DryRun',[string]$Root='C:\GPT-MultiBody\v1.0.1',[string]$StateDir='C:\ProgramData\GPT-MultiBody\heartbeat')
$name='GPT-MultiBody-Heartbeat-v1.0.1'; $task="`"$env:SystemRoot\py.exe`" `"$Root\daemon\heartbeat_daemon.py`" --node-id office-4090 --role EXTENSION --state-dir `"$StateDir`" --interval 15"
if($Action -eq 'DryRun'){ Write-Output (@{action=$Action;task=$name;command=$task;touches=@('heartbeat state/log only','no AI/Ollama/CUDA/NVIDIA/user project config')}|ConvertTo-Json); exit 0 }
if($Action -eq 'Disable'){ Disable-ScheduledTask -TaskName $name -ErrorAction Stop; exit 0 }
if($Action -eq 'Uninstall'){ Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction Stop; exit 0 }
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$a=New-ScheduledTaskAction -Execute "$env:SystemRoot\py.exe" -Argument "`"$Root\daemon\heartbeat_daemon.py`" --node-id office-4090 --role EXTENSION --state-dir `"$StateDir`" --interval 15"
$t=New-ScheduledTaskTrigger -AtStartup; $s=New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $name -Action $a -Trigger $t -Settings $s -User 'SYSTEM' -RunLevel Limited -Force | Out-Null
