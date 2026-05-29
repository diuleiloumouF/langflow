. $PSScriptRoot\start_dev.ps1

function Get-TestBashPath {
    Get-GitBashPath
}

Describe "Get-GitBashPath" {
    It "returns a Git bash.exe executable instead of git-bash.exe" {
        $result = Get-GitBashPath

        $result | Should Match "\\Git\\"
        $result | Should Match "bash\.exe$"
        $result | Should Not Match "git-bash\.exe$"
    }
}

Describe "script path resolution" {
    It "resolves the repository root from the script location" {
        $script:StartDevProjectRoot.Path | Should Be (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    }
}

Describe "New-GitBashCommand" {
    It "produces a bash command string with the requested target and title" {
        $command = New-GitBashCommand -ProjectPath "/e/workspace/studyDemo/langflow" -Target "backend" -Title "Langflow Backend"

        $command | Should Match "make backend"
        $command | Should Match "Langflow Backend exited with status"
        $command | Should Match "cd '/e/workspace/studyDemo/langflow'"
    }
}

Describe "Write-LauncherScripts" {
    It "writes cmd and bash launcher files that point to the requested target" {
        $paths = Write-LauncherScripts -ProjectPath "/e/workspace/studyDemo/langflow" -Target "frontend" -Title "Langflow Frontend" -BashPath "C:\Program Files\Git\bin\bash.exe"

        Test-Path $paths.Bash | Should Be $true
        Test-Path $paths.Cmd | Should Be $true
        (Get-Content $paths.Bash -Raw) | Should Match "make frontend"
        (Get-Content $paths.Cmd -Raw) | Should Match ([regex]::Escape('"C:\Program Files\Git\bin\bash.exe" --login -i'))
    }
}
