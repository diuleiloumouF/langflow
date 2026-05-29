#!/usr/bin/env pwsh

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script:StartDevScriptDir = Split-Path -Parent $PSCommandPath
$script:StartDevProjectRoot = Resolve-Path (Join-Path $script:StartDevScriptDir "..\..")

function Get-GitBashPath {
    $candidates = @(
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files\Git\usr\bin\bash.exe",
        "C:\Program Files (x86)\Git\bin\bash.exe",
        "C:\Program Files (x86)\Git\usr\bin\bash.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $bashCommand = Get-Command bash.exe -ErrorAction SilentlyContinue
    if ($bashCommand -and $bashCommand.Source -match "\\Git\\") {
        return $bashCommand.Source
    }

    throw "Git Bash bash.exe was not found. Install Git for Windows or add bash.exe to PATH."
}

function Convert-ToGitBashPath([string]$WindowsPath) {
    $resolvedPath = (Resolve-Path $WindowsPath).Path
    $normalizedPath = $resolvedPath -replace "\\", "/"

    if ($normalizedPath -match "^([A-Za-z]):(.*)$") {
        return "/$($matches[1].ToLower())$($matches[2])"
    }

    throw "Unsupported path format: $resolvedPath"
}

function New-GitBashCommand([string]$ProjectPath, [string]$Target, [string]$Title) {
    $template = @'
printf '\033]0;{0}\007'
cd '{1}' || exit 1
command -v make >/dev/null 2>&1 || {{
  echo 'make was not found in Git Bash.'
  read -n 1 -s -r -p 'Press any key to close...'
  exit 1
}}
make {2}
status=$?
echo
echo '{0} exited with status' $status
read -n 1 -s -r -p 'Press any key to close...'
exit $status
'@

    return [string]::Format($template, $Title, $ProjectPath, $Target)
}

function New-LauncherScriptPaths([string]$Target) {
    $tempRoot = Join-Path $env:TEMP "langflow-start-dev"
    if (-not (Test-Path $tempRoot)) {
        New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    }

    $runId = [guid]::NewGuid().ToString("N")

    return @{
        Bash = Join-Path $tempRoot "$Target-$runId.sh"
        Cmd = Join-Path $tempRoot "$Target-$runId.cmd"
    }
}

function Write-LauncherScripts([string]$ProjectPath, [string]$Target, [string]$Title, [string]$BashPath) {
    $paths = New-LauncherScriptPaths -Target $Target
    $bashCommand = New-GitBashCommand -ProjectPath $ProjectPath -Target $Target -Title $Title

    Set-Content -Path $paths.Bash -Value $bashCommand -Encoding ASCII

    $cmdContent = @"
@echo off
cd /d $($script:StartDevProjectRoot.Path)
"$BashPath" --login -i "$($paths.Bash)"
"@

    Set-Content -Path $paths.Cmd -Value $cmdContent -Encoding ASCII
    return $paths
}

function Start-LangflowDev {
    $projectRoot = $script:StartDevProjectRoot
    $projectRootForBash = Convert-ToGitBashPath $projectRoot
    $bashPath = Get-GitBashPath

    Write-Host "Using Git Bash at: $bashPath" -ForegroundColor Cyan
    Write-Host "Project root: $projectRoot" -ForegroundColor Cyan
    Write-Host "Starting Langflow backend and frontend in separate Git Bash windows..." -ForegroundColor Green

    $backendScripts = Write-LauncherScripts -ProjectPath $projectRootForBash -Target "backend" -Title "Langflow Backend" -BashPath $bashPath
    $frontendScripts = Write-LauncherScripts -ProjectPath $projectRootForBash -Target "frontend" -Title "Langflow Frontend" -BashPath $bashPath

    Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", $backendScripts.Cmd) -WorkingDirectory $projectRoot
    Start-Sleep -Milliseconds 500
    Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", $frontendScripts.Cmd) -WorkingDirectory $projectRoot

    Write-Host ""
    Write-Host "Backend:  http://localhost:7860" -ForegroundColor Yellow
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
    Write-Host "Use the frontend URL for hot reload." -ForegroundColor Yellow
}

if ($MyInvocation.InvocationName -ne ".") {
    Start-LangflowDev
}
