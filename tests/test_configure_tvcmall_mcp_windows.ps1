[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dialog', 'new-config', 'preserve-config', 'invalid-config', 'idempotent')]
    [string]$Case,

    [Parameter(Mandatory = $true)]
    [string]$TempRoot,

    [Parameter(Mandatory = $true)]
    [string]$CodexExecutable
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$productionScript = Join-Path $PSScriptRoot '..\.agents\skills\query-tvcmall-customer-data\scripts\configure_tvcmall_mcp_windows.ps1'
. $productionScript
Add-Type -AssemblyName System.Windows.Forms

$fakeKey = 'tmcp_v1_demo.secret'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

function Assert-Equal {
    param($Expected, $Actual, [string]$Message)
    if ($Expected -cne $Actual) {
        throw $Message
    }
}

function Assert-RejectedKey {
    param([string]$Value)
    try {
        $null = Normalize-TvcmallApiKey -Value $Value
    }
    catch {
        if ($Value.Length -gt 0) {
            Assert-True (-not $_.Exception.Message.Contains($Value)) 'A validation error exposed the submitted value.'
        }
        return
    }
    throw 'An invalid API Key was accepted.'
}

function Get-Control {
    param([System.Windows.Forms.Control]$Form, [string]$Name)
    $matches = $Form.Controls.Find($Name, $true)
    Assert-Equal 1 $matches.Count "Expected one control named $Name."
    return $matches[0]
}

switch ($Case) {
    'dialog' {
        Assert-Equal $fakeKey (Normalize-TvcmallApiKey -Value " `r`n$fakeKey`t ") 'Surrounding whitespace was not removed.'
        foreach ($invalid in @(
            '',
            'TMCP_v1_demo.secret',
            'Bearer tmcp_v1_demo.secret',
            'tmcp_catalog.read',
            'tmcp_v1_.secret',
            'tmcp_v1_demo.',
            'tmcp_v1_demo.extra.secret',
            "tmcp_v1_demo.$([char]0x00E9)",
            "tmcp_v1_demo.`u{0016}secret",
            "tmcp_v1_demo.`nsecret"
        )) {
            Assert-RejectedKey -Value $invalid
        }

        $commandProbe = Join-Path $TempRoot 'command-probe'
        $isolatedHome = Join-Path $commandProbe 'isolated home'
        [System.IO.Directory]::CreateDirectory($isolatedHome) | Out-Null
        $fakeCodex = Join-Path $commandProbe 'fake-codex.cmd'
        $observedWorkingDirectory = Join-Path $commandProbe 'observed-working-directory.txt'
        $fakeCodexSource = "@echo off`r`necho %CD%> `"$observedWorkingDirectory`"`r`nexit /b 0`r`n"
        [System.IO.File]::WriteAllText($fakeCodex, $fakeCodexSource, [System.Text.Encoding]::ASCII)
        $originalWorkingDirectory = (Get-Location).Path
        $probeExitCode = Invoke-TvcmallCodexCommand `
            -CodexExecutable $fakeCodex `
            -WorkingHome $isolatedHome `
            -Arguments @('mcp', 'list')
        Assert-Equal 0 $probeExitCode 'The command probe failed.'
        Assert-Equal $isolatedHome ([System.IO.File]::ReadAllText($observedWorkingDirectory).Trim()) 'Codex was not isolated from the caller working directory.'
        Assert-Equal $originalWorkingDirectory (Get-Location).Path 'The caller working directory was not restored.'

        $state = @{ Calls = 0; Received = $null; Messages = @() }
        $configure = {
            param($ConfigPath, $ApiKey, $CodexPath)
            $state.Calls += 1
            $state.Received = $ApiKey
            return [pscustomobject]@{ ConfigPath = $ConfigPath; BackupPath = $null; Changed = $true }
        }.GetNewClosure()
        $clipboard = { return "  $fakeKey`r`n" }.GetNewClosure()
        $message = {
            param($Text, $Title, $Icon)
            $state.Messages += [string]$Text
        }.GetNewClosure()

        $form = New-TvcmallSetupForm `
            -ConfigPath (Join-Path $TempRoot 'dialog\config.toml') `
            -CodexExecutable $CodexExecutable `
            -ConfigureAction $configure `
            -ClipboardAction $clipboard `
            -MessageAction $message
        try {
            $form.ShowInTaskbar = $false
            $form.Opacity = 0
            $form.Show()
            [System.Windows.Forms.Application]::DoEvents()
            $apiKeyBox = Get-Control -Form $form -Name 'ApiKeyTextBox'
            $pasteButton = Get-Control -Form $form -Name 'PasteButton'
            $toggleButton = Get-Control -Form $form -Name 'ToggleVisibilityButton'
            $consent = Get-Control -Form $form -Name 'ConsentCheckBox'
            $saveButton = Get-Control -Form $form -Name 'SaveButton'
            $statusLabel = Get-Control -Form $form -Name 'StatusLabel'

            Assert-True $apiKeyBox.UseSystemPasswordChar 'The API Key field is not masked by default.'
            $pasteButton.PerformClick()
            Assert-True $apiKeyBox.UseSystemPasswordChar 'Pasting disabled the password mask.'
            Assert-True $statusLabel.Text.StartsWith('Received ') 'The dialog did not confirm that characters were received.'
            Assert-True (-not $statusLabel.Text.Contains($fakeKey)) 'The status label exposed the API Key.'

            $toggleButton.PerformClick()
            Assert-True (-not $apiKeyBox.UseSystemPasswordChar) 'The explicit Show action did not reveal the field.'
            $toggleButton.PerformClick()
            Assert-True $apiKeyBox.UseSystemPasswordChar 'The Hide action did not restore the mask.'

            $consent.Checked = $true
            Assert-True $saveButton.Enabled 'Save was not enabled after input and plaintext-storage consent.'
            $saveButton.PerformClick()
            Assert-Equal 1 $state.Calls 'The valid Key was not submitted exactly once.'
            Assert-Equal $fakeKey $state.Received 'The normalized Key was not submitted.'
            Assert-Equal '' $apiKeyBox.Text 'The Key field was not cleared after configuration.'
            Assert-True (-not (($state.Messages -join "`n").Contains($fakeKey))) 'A dialog message exposed the API Key.'
            Assert-True (-not (($state.Messages -join "`n").Contains('`r`n'))) 'The success dialog contains literal newline escape text.'
        }
        finally {
            $form.Dispose()
        }

        $invalidState = @{ Calls = 0 }
        $invalidConfigure = {
            param($ConfigPath, $ApiKey, $CodexPath)
            $invalidState.Calls += 1
        }.GetNewClosure()
        $invalidForm = New-TvcmallSetupForm `
            -ConfigPath (Join-Path $TempRoot 'invalid-dialog\config.toml') `
            -CodexExecutable $CodexExecutable `
            -ConfigureAction $invalidConfigure `
            -ClipboardAction { return 'not-a-personal-pat' } `
            -MessageAction { param($Text, $Title, $Icon) }
        try {
            $invalidForm.ShowInTaskbar = $false
            $invalidForm.Opacity = 0
            $invalidForm.Show()
            [System.Windows.Forms.Application]::DoEvents()
            $invalidKeyBox = Get-Control -Form $invalidForm -Name 'ApiKeyTextBox'
            (Get-Control -Form $invalidForm -Name 'PasteButton').PerformClick()
            (Get-Control -Form $invalidForm -Name 'ConsentCheckBox').Checked = $true
            (Get-Control -Form $invalidForm -Name 'SaveButton').PerformClick()
            Assert-Equal 0 $invalidState.Calls 'Invalid input reached the configuration callback.'
            Assert-True (-not $invalidForm.IsDisposed) 'The dialog closed after invalid input instead of allowing a retry.'
            Assert-True (-not (Get-Control -Form $invalidForm -Name 'ValidationLabel').Text.Contains($invalidKeyBox.Text)) 'Validation text exposed invalid input.'
        }
        finally {
            $invalidKeyBox.Clear()
            $invalidForm.Dispose()
        }

        $failedForm = New-TvcmallSetupForm `
            -ConfigPath (Join-Path $TempRoot 'failed-dialog\config.toml') `
            -CodexExecutable $CodexExecutable `
            -ConfigureAction { param($ConfigPath, $ApiKey, $CodexPath) throw 'A safe simulated write failure occurred.' } `
            -ClipboardAction { return $fakeKey }.GetNewClosure() `
            -MessageAction { param($Text, $Title, $Icon) }
        try {
            $failedForm.ShowInTaskbar = $false
            $failedForm.Opacity = 0
            $failedForm.Show()
            [System.Windows.Forms.Application]::DoEvents()
            $failedKeyBox = Get-Control -Form $failedForm -Name 'ApiKeyTextBox'
            (Get-Control -Form $failedForm -Name 'PasteButton').PerformClick()
            (Get-Control -Form $failedForm -Name 'ConsentCheckBox').Checked = $true
            (Get-Control -Form $failedForm -Name 'SaveButton').PerformClick()
            Assert-Equal '' $failedKeyBox.Text 'The Key field was not cleared after a write failure.'
            Assert-True (-not $failedForm.IsDisposed) 'The dialog closed after a write failure instead of allowing a retry.'
            Assert-True (Get-Control -Form $failedForm -Name 'ValidationLabel').Text.Contains('safe simulated write failure') 'The write failure message did not remain visible.'
        }
        finally {
            $failedKeyBox.Clear()
            $failedForm.Dispose()
        }
    }

    'new-config' {
        $path = Join-Path $TempRoot 'new\config.toml'
        $result = Set-TvcmallMcpConfigFile -ConfigPath $path -ApiKey $fakeKey -CodexExecutable $CodexExecutable
        Assert-True $result.Changed 'A new configuration was not reported as changed.'
        Assert-True (Test-Path -LiteralPath $path -PathType Leaf) 'The new configuration was not created.'
        Assert-True (-not (Test-Path -LiteralPath "$path.bak")) 'A backup was created for a new configuration.'
    }

    'preserve-config' {
        $directory = Join-Path $TempRoot 'preserve'
        [System.IO.Directory]::CreateDirectory($directory) | Out-Null
        $path = Join-Path $directory 'config.toml'
        $source = @'
model = "gpt-5"
message = """
[mcp_servers.tvcmall]
This is documentation, not a TOML table.
"""

[mcp_servers.other]
url = "https://example.com/mcp"

[mcp_servers."tvcmall"]
url = "https://old.invalid/mcp"

[mcp_servers."tvcmall".http_headers]
OLD = "value"

[[custom_profiles]]
name = "first"

[[custom_profiles]]
name = "second"
'@
        [System.IO.File]::WriteAllText($path, $source, [System.Text.UTF8Encoding]::new($false))
        $result = Set-TvcmallMcpConfigFile -ConfigPath $path -ApiKey $fakeKey -CodexExecutable $CodexExecutable
        Assert-True $result.Changed 'The existing configuration was not reported as changed.'
        Assert-Equal "$path.bak" $result.BackupPath 'The backup path was not reported.'
        Assert-Equal $source ([System.IO.File]::ReadAllText("$path.bak")) 'The backup did not preserve the original configuration.'
    }

    'invalid-config' {
        $directory = Join-Path $TempRoot 'invalid'
        [System.IO.Directory]::CreateDirectory($directory) | Out-Null
        $path = Join-Path $directory 'config.toml'
        [System.IO.File]::WriteAllText($path, '[broken', [System.Text.UTF8Encoding]::new($false))
        $failed = $false
        try {
            $null = Set-TvcmallMcpConfigFile -ConfigPath $path -ApiKey $fakeKey -CodexExecutable $CodexExecutable
        }
        catch {
            $failed = $true
            Assert-True (-not $_.Exception.Message.Contains($fakeKey)) 'A configuration error exposed the API Key.'
        }
        Assert-True $failed 'Invalid TOML was accepted.'
        Assert-Equal '[broken' ([System.IO.File]::ReadAllText($path)) 'Invalid TOML was modified.'
        Assert-True (-not (Test-Path -LiteralPath "$path.bak")) 'Invalid TOML produced a backup.'
    }

    'idempotent' {
        $directory = Join-Path $TempRoot 'idempotent'
        [System.IO.Directory]::CreateDirectory($directory) | Out-Null
        $path = Join-Path $directory 'config.toml'
        [System.IO.File]::WriteAllText($path, "model = `"gpt-5`"`r`n", [System.Text.UTF8Encoding]::new($false))
        $first = Set-TvcmallMcpConfigFile -ConfigPath $path -ApiKey $fakeKey -CodexExecutable $CodexExecutable
        Assert-True $first.Changed 'The first update was not reported as changed.'
        $backupPath = "$path.bak"
        $backupTimestamp = [System.IO.File]::GetLastWriteTimeUtc($backupPath)
        $second = Set-TvcmallMcpConfigFile -ConfigPath $path -ApiKey $fakeKey -CodexExecutable $CodexExecutable
        Assert-True (-not $second.Changed) 'The repeated update was not idempotent.'
        Assert-Equal $null $second.BackupPath 'The repeated update reported a backup.'
        Assert-Equal $backupTimestamp ([System.IO.File]::GetLastWriteTimeUtc($backupPath)) 'The repeated update refreshed the backup.'
    }
}

Write-Output "PASS: $Case"
