Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:TvcmallMcpUrl = 'https://openai.tvc-mall.com/mcp'
$script:TvcmallApiKeyPattern = '\Atmcp_v1_[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\z'

if ($null -eq ('TvcmallSetup.NativeMethods' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace TvcmallSetup
{
    public static class NativeMethods
    {
        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr windowHandle, int command);

        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr windowHandle);
    }
}
'@
}

function Normalize-TvcmallApiKey {
    [CmdletBinding()]
    param(
        [AllowEmptyString()]
        [string]$Value
    )

    $normalized = $Value.Trim()
    $isValid = [System.Text.RegularExpressions.Regex]::IsMatch(
        $normalized,
        $script:TvcmallApiKeyPattern,
        [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
    )
    if (-not $isValid) {
        throw [System.ArgumentException]::new(
            'Paste the complete personal PAT beginning with tmcp_v1_. It must contain exactly one dot and no internal spaces.'
        )
    }
    return $normalized
}

function Resolve-TvcmallConfigPath {
    [CmdletBinding()]
    param()

    $configuredHome = [System.Environment]::GetEnvironmentVariable('CODEX_HOME', 'Process')
    if ([string]::IsNullOrWhiteSpace($configuredHome)) {
        $configuredHome = Join-Path ([System.Environment]::GetFolderPath('UserProfile')) '.codex'
    }
    return [System.IO.Path]::GetFullPath((Join-Path $configuredHome 'config.toml'))
}

function Resolve-TvcmallCodexExecutable {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string]$ExplicitPath
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        if ([System.IO.File]::Exists($ExplicitPath)) {
            return [System.IO.Path]::GetFullPath($ExplicitPath)
        }
        $explicitCommand = Get-Command -Name $ExplicitPath -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $explicitCommand -and -not [string]::IsNullOrWhiteSpace($explicitCommand.Source)) {
            return $explicitCommand.Source
        }
    }

    foreach ($commandName in @('codex.exe', 'codex.cmd', 'codex')) {
        $command = Get-Command -Name $commandName -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $command -and -not [string]::IsNullOrWhiteSpace($command.Source)) {
            return $command.Source
        }
    }

    throw [System.InvalidOperationException]::new(
        'The Codex command was not found. Start this dialog from Codex, then try again.'
    )
}

function Invoke-TvcmallCodexCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CodexExecutable,

        [Parameter(Mandatory = $true)]
        [string]$WorkingHome,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $previousHome = [System.Environment]::GetEnvironmentVariable('CODEX_HOME', 'Process')
    $previousPreference = $ErrorActionPreference
    $previousLocation = (Get-Location).Path
    try {
        [System.Environment]::SetEnvironmentVariable('CODEX_HOME', $WorkingHome, 'Process')
        Set-Location -LiteralPath $WorkingHome
        $ErrorActionPreference = 'Continue'
        & $CodexExecutable @Arguments *> $null
        return [int]$LASTEXITCODE
    }
    catch {
        return -1
    }
    finally {
        $ErrorActionPreference = $previousPreference
        Set-Location -LiteralPath $previousLocation
        [System.Environment]::SetEnvironmentVariable('CODEX_HOME', $previousHome, 'Process')
    }
}

function Add-TvcmallHeaderToConfig {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$ApiKey
    )

    $normalized = Normalize-TvcmallApiKey -Value $ApiKey
    $pattern = '^\[mcp_servers\.tvcmall\][ \t]*(?:#[^\r\n]*)?(?=\r?$)'
    $options = [System.Text.RegularExpressions.RegexOptions]::Multiline -bor
        [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
    $matches = [System.Text.RegularExpressions.Regex]::Matches($Source, $pattern, $options)
    if ($matches.Count -lt 1) {
        throw [System.InvalidOperationException]::new(
            'Codex did not create the expected TVCMall MCP section. No changes were applied.'
        )
    }

    # Codex appends the section it creates, so the last exact header is authoritative even
    # when an unrelated multiline string contains header-like text.
    $header = $matches[$matches.Count - 1]
    $lineEnd = $header.Index + $header.Length
    $newline = if ($Source.Contains("`r`n")) { "`r`n" } else { "`n" }
    if ($lineEnd + 1 -lt $Source.Length -and $Source.Substring($lineEnd, 2) -eq "`r`n") {
        $insertAt = $lineEnd + 2
        $prefix = ''
    }
    elseif ($lineEnd -lt $Source.Length -and $Source[$lineEnd] -eq "`n") {
        $insertAt = $lineEnd + 1
        $prefix = ''
    }
    else {
        $insertAt = $lineEnd
        $prefix = $newline
    }

    $headerLine = 'http_headers = { "TVCMALL_API_KEY" = "' + $normalized + '" }' + $newline
    return $Source.Insert($insertAt, $prefix + $headerLine)
}

function New-TvcmallCandidateConfigBytes {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [byte[]]$SourceBytes,

        [AllowNull()]
        [string]$CodexExecutable,

        [Parameter(Mandatory = $true)]
        [string]$ApiKey
    )

    $normalized = Normalize-TvcmallApiKey -Value $ApiKey
    $resolvedCodex = Resolve-TvcmallCodexExecutable -ExplicitPath $CodexExecutable
    $workingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('tvcmall-mcp-' + [System.Guid]::NewGuid().ToString('N'))
    $candidateBytes = $null
    $cleanupFailure = $null

    [System.IO.Directory]::CreateDirectory($workingRoot) | Out-Null
    try {
        $candidatePath = Join-Path $workingRoot 'config.toml'
        [System.IO.File]::WriteAllBytes($candidatePath, $SourceBytes)

        $validCode = Invoke-TvcmallCodexCommand `
            -CodexExecutable $resolvedCodex `
            -WorkingHome $workingRoot `
            -Arguments @('mcp', 'list')
        if ($validCode -ne 0) {
            throw [System.InvalidOperationException]::new(
                'The existing Codex config is invalid or cannot be loaded. No changes were applied.'
            )
        }

        $existingCode = Invoke-TvcmallCodexCommand `
            -CodexExecutable $resolvedCodex `
            -WorkingHome $workingRoot `
            -Arguments @('mcp', 'get', 'tvcmall')
        if ($existingCode -eq 0) {
            $removeCode = Invoke-TvcmallCodexCommand `
                -CodexExecutable $resolvedCodex `
                -WorkingHome $workingRoot `
                -Arguments @('mcp', 'remove', 'tvcmall')
            if ($removeCode -ne 0) {
                throw [System.InvalidOperationException]::new(
                    'Codex could not replace the existing TVCMall MCP entry. No changes were applied.'
                )
            }
        }

        $addCode = Invoke-TvcmallCodexCommand `
            -CodexExecutable $resolvedCodex `
            -WorkingHome $workingRoot `
            -Arguments @('mcp', 'add', 'tvcmall', '--url', $script:TvcmallMcpUrl)
        if ($addCode -ne 0) {
            throw [System.InvalidOperationException]::new(
                'Codex could not create the TVCMall MCP entry. No changes were applied.'
            )
        }

        $strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
        $candidateText = $strictUtf8.GetString([System.IO.File]::ReadAllBytes($candidatePath))
        $candidateText = Add-TvcmallHeaderToConfig -Source $candidateText -ApiKey $normalized
        $candidateBytes = [System.Text.UTF8Encoding]::new($false).GetBytes($candidateText)
        [System.IO.File]::WriteAllBytes($candidatePath, $candidateBytes)

        $finalCode = Invoke-TvcmallCodexCommand `
            -CodexExecutable $resolvedCodex `
            -WorkingHome $workingRoot `
            -Arguments @('mcp', 'list')
        if ($finalCode -ne 0) {
            throw [System.InvalidOperationException]::new(
                'Codex rejected the generated MCP configuration. No changes were applied.'
            )
        }
    }
    finally {
        if ([System.IO.Directory]::Exists($workingRoot)) {
            try {
                [System.IO.Directory]::Delete($workingRoot, $true)
            }
            catch {
                $cleanupFailure = $_
            }
        }
    }

    if ($null -ne $cleanupFailure) {
        throw [System.IO.IOException]::new(
            "A temporary configuration could not be removed. Delete this directory before retrying: $workingRoot"
        )
    }
    if ($null -eq $candidateBytes) {
        throw [System.InvalidOperationException]::new(
            'Codex could not prepare the MCP configuration. No changes were applied.'
        )
    }
    return ,$candidateBytes
}

function Test-TvcmallByteArraysEqual {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [byte[]]$Left,

        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [byte[]]$Right
    )

    if ($Left.Length -ne $Right.Length) {
        return $false
    }
    for ($index = 0; $index -lt $Left.Length; $index += 1) {
        if ($Left[$index] -ne $Right[$index]) {
            return $false
        }
    }
    return $true
}

function Write-TvcmallStagingFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [byte[]]$Content
    )

    $stream = [System.IO.FileStream]::new(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($Content, 0, $Content.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
}

function Set-TvcmallMcpConfigFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath,

        [Parameter(Mandatory = $true)]
        [string]$ApiKey,

        [AllowNull()]
        [string]$CodexExecutable
    )

    $normalized = Normalize-TvcmallApiKey -Value $ApiKey
    $fullPath = [System.IO.Path]::GetFullPath($ConfigPath)
    $existed = [System.IO.File]::Exists($fullPath)
    [byte[]]$originalBytes = @()
    if ($existed) {
        $originalBytes = [System.IO.File]::ReadAllBytes($fullPath)
    }

    $candidateBytes = New-TvcmallCandidateConfigBytes `
        -SourceBytes $originalBytes `
        -CodexExecutable $CodexExecutable `
        -ApiKey $normalized
    if (Test-TvcmallByteArraysEqual -Left $originalBytes -Right $candidateBytes) {
        return [pscustomobject]@{
            ConfigPath = $fullPath
            BackupPath = $null
            Changed = $false
        }
    }

    $configDirectory = [System.IO.Path]::GetDirectoryName($fullPath)
    [System.IO.Directory]::CreateDirectory($configDirectory) | Out-Null
    $stagingPath = Join-Path $configDirectory ('.' + [System.IO.Path]::GetFileName($fullPath) + '.' + [System.Guid]::NewGuid().ToString('N') + '.tmp')
    $backupPath = if ($existed) { $fullPath + '.bak' } else { $null }

    try {
        Write-TvcmallStagingFile -Path $stagingPath -Content $candidateBytes

        $stillExists = [System.IO.File]::Exists($fullPath)
        if ($stillExists -ne $existed) {
            throw [System.InvalidOperationException]::new(
                'The Codex config changed during setup. No changes were applied.'
            )
        }
        if ($existed) {
            $currentBytes = [System.IO.File]::ReadAllBytes($fullPath)
            if (-not (Test-TvcmallByteArraysEqual -Left $originalBytes -Right $currentBytes)) {
                throw [System.InvalidOperationException]::new(
                    'The Codex config changed during setup. No changes were applied.'
                )
            }
            [System.IO.File]::Replace($stagingPath, $fullPath, $backupPath, $true)
        }
        else {
            [System.IO.File]::Move($stagingPath, $fullPath)
        }
    }
    catch [System.InvalidOperationException] {
        throw
    }
    catch {
        throw [System.IO.IOException]::new(
            'The Codex config could not be written. The original file was not intentionally changed.'
        )
    }
    finally {
        if ([System.IO.File]::Exists($stagingPath)) {
            [System.IO.File]::Delete($stagingPath)
        }
    }

    return [pscustomobject]@{
        ConfigPath = $fullPath
        BackupPath = $backupPath
        Changed = $true
    }
}

function New-TvcmallSetupForm {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath,

        [AllowNull()]
        [string]$CodexExecutable,

        [scriptblock]$ConfigureAction,

        [scriptblock]$ClipboardAction,

        [scriptblock]$MessageAction
    )

    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()

    if ($null -eq $ConfigureAction) {
        $ConfigureAction = {
            param($TargetPath, $SubmittedKey, $CodexPath)
            return Set-TvcmallMcpConfigFile `
                -ConfigPath $TargetPath `
                -ApiKey $SubmittedKey `
                -CodexExecutable $CodexPath
        }
    }
    if ($null -eq $ClipboardAction) {
        $ClipboardAction = {
            if ([System.Windows.Forms.Clipboard]::ContainsText()) {
                return [System.Windows.Forms.Clipboard]::GetText()
            }
            return ''
        }
    }
    if ($null -eq $MessageAction) {
        $MessageAction = {
            param($Text, $Title, $Icon)
            [System.Windows.Forms.MessageBox]::Show(
                $Text,
                $Title,
                [System.Windows.Forms.MessageBoxButtons]::OK,
                $Icon
            ) | Out-Null
        }
    }

    $form = [System.Windows.Forms.Form]::new()
    $form.Name = 'TvcmallSetupForm'
    $form.Text = 'Configure TVCMall MCP'
    $form.ClientSize = [System.Drawing.Size]::new(640, 455)
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    $form.ShowInTaskbar = $true
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.TopMost = $true
    $form.AutoScaleMode = [System.Windows.Forms.AutoScaleMode]::Dpi

    $heading = [System.Windows.Forms.Label]::new()
    $heading.Location = [System.Drawing.Point]::new(24, 20)
    $heading.Size = [System.Drawing.Size]::new(590, 30)
    $heading.Font = [System.Drawing.Font]::new('Segoe UI', 14, [System.Drawing.FontStyle]::Bold)
    $heading.Text = 'Connect Codex to TVCMall'
    $form.Controls.Add($heading)

    $description = [System.Windows.Forms.Label]::new()
    $description.Location = [System.Drawing.Point]::new(26, 58)
    $description.Size = [System.Drawing.Size]::new(585, 42)
    $description.Text = 'Paste the complete personal PAT. It remains in this local process and is written only to the Codex configuration shown below.'
    $form.Controls.Add($description)

    $endpointCaption = [System.Windows.Forms.Label]::new()
    $endpointCaption.Location = [System.Drawing.Point]::new(26, 108)
    $endpointCaption.Size = [System.Drawing.Size]::new(90, 20)
    $endpointCaption.Text = 'MCP endpoint'
    $form.Controls.Add($endpointCaption)

    $endpointBox = [System.Windows.Forms.TextBox]::new()
    $endpointBox.Location = [System.Drawing.Point]::new(26, 131)
    $endpointBox.Size = [System.Drawing.Size]::new(585, 23)
    $endpointBox.ReadOnly = $true
    $endpointBox.Text = $script:TvcmallMcpUrl
    $form.Controls.Add($endpointBox)

    $pathCaption = [System.Windows.Forms.Label]::new()
    $pathCaption.Location = [System.Drawing.Point]::new(26, 166)
    $pathCaption.Size = [System.Drawing.Size]::new(130, 20)
    $pathCaption.Text = 'Codex config path'
    $form.Controls.Add($pathCaption)

    $pathBox = [System.Windows.Forms.TextBox]::new()
    $pathBox.Location = [System.Drawing.Point]::new(26, 189)
    $pathBox.Size = [System.Drawing.Size]::new(585, 23)
    $pathBox.ReadOnly = $true
    $pathBox.Text = $ConfigPath
    $form.Controls.Add($pathBox)

    $apiKeyCaption = [System.Windows.Forms.Label]::new()
    $apiKeyCaption.Location = [System.Drawing.Point]::new(26, 224)
    $apiKeyCaption.Size = [System.Drawing.Size]::new(155, 20)
    $apiKeyCaption.Text = 'TVCMALL_API_KEY'
    $form.Controls.Add($apiKeyCaption)

    $apiKeyBox = [System.Windows.Forms.TextBox]::new()
    $apiKeyBox.Name = 'ApiKeyTextBox'
    $apiKeyBox.Location = [System.Drawing.Point]::new(26, 247)
    $apiKeyBox.Size = [System.Drawing.Size]::new(420, 23)
    $apiKeyBox.UseSystemPasswordChar = $true
    $form.Controls.Add($apiKeyBox)

    $pasteButton = [System.Windows.Forms.Button]::new()
    $pasteButton.Name = 'PasteButton'
    $pasteButton.Location = [System.Drawing.Point]::new(454, 245)
    $pasteButton.Size = [System.Drawing.Size]::new(75, 27)
    $pasteButton.Text = 'Paste'
    $form.Controls.Add($pasteButton)

    $toggleButton = [System.Windows.Forms.Button]::new()
    $toggleButton.Name = 'ToggleVisibilityButton'
    $toggleButton.Location = [System.Drawing.Point]::new(536, 245)
    $toggleButton.Size = [System.Drawing.Size]::new(75, 27)
    $toggleButton.Text = 'Show'
    $form.Controls.Add($toggleButton)

    $statusLabel = [System.Windows.Forms.Label]::new()
    $statusLabel.Name = 'StatusLabel'
    $statusLabel.Location = [System.Drawing.Point]::new(26, 278)
    $statusLabel.Size = [System.Drawing.Size]::new(585, 20)
    $statusLabel.ForeColor = [System.Drawing.Color]::DimGray
    $statusLabel.Text = 'No characters received.'
    $form.Controls.Add($statusLabel)

    $validationLabel = [System.Windows.Forms.Label]::new()
    $validationLabel.Name = 'ValidationLabel'
    $validationLabel.Location = [System.Drawing.Point]::new(26, 300)
    $validationLabel.Size = [System.Drawing.Size]::new(585, 36)
    $validationLabel.ForeColor = [System.Drawing.Color]::Firebrick
    $validationLabel.Text = ''
    $form.Controls.Add($validationLabel)

    $consent = [System.Windows.Forms.CheckBox]::new()
    $consent.Name = 'ConsentCheckBox'
    $consent.Location = [System.Drawing.Point]::new(26, 340)
    $consent.Size = [System.Drawing.Size]::new(585, 42)
    $consent.Text = 'I understand that this PAT and the replaceable config.toml.bak backup are stored unencrypted on this computer.'
    $form.Controls.Add($consent)

    $saveButton = [System.Windows.Forms.Button]::new()
    $saveButton.Name = 'SaveButton'
    $saveButton.Location = [System.Drawing.Point]::new(442, 402)
    $saveButton.Size = [System.Drawing.Size]::new(82, 30)
    $saveButton.Text = 'Save'
    $saveButton.Enabled = $false
    $form.Controls.Add($saveButton)

    $cancelButton = [System.Windows.Forms.Button]::new()
    $cancelButton.Name = 'CancelButton'
    $cancelButton.Location = [System.Drawing.Point]::new(529, 402)
    $cancelButton.Size = [System.Drawing.Size]::new(82, 30)
    $cancelButton.Text = 'Cancel'
    $cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.Controls.Add($cancelButton)

    $form.AcceptButton = $saveButton
    $form.CancelButton = $cancelButton

    $updateState = {
        $length = $apiKeyBox.TextLength
        $statusLabel.Text = if ($length -eq 0) {
            'No characters received.'
        }
        else {
            "Received $length characters."
        }
        $validationLabel.Text = ''
        $saveButton.Enabled = $consent.Checked -and $length -gt 0
    }.GetNewClosure()

    $apiKeyBox.Add_TextChanged($updateState)
    $consent.Add_CheckedChanged($updateState)
    $pasteButton.Add_Click(({
        try {
            $apiKeyBox.Text = [string](& $ClipboardAction)
            $apiKeyBox.SelectionStart = $apiKeyBox.TextLength
            $apiKeyBox.Focus()
        }
        catch {
            $validationLabel.Text = 'The clipboard could not be read. Use Ctrl+V in the masked field.'
        }
    }).GetNewClosure())
    $toggleButton.Add_Click(({
        $apiKeyBox.UseSystemPasswordChar = -not $apiKeyBox.UseSystemPasswordChar
        $toggleButton.Text = if ($apiKeyBox.UseSystemPasswordChar) { 'Show' } else { 'Hide' }
        $apiKeyBox.Focus()
    }).GetNewClosure())
    $saveButton.Add_Click(({
        try {
            $normalized = Normalize-TvcmallApiKey -Value $apiKeyBox.Text
        }
        catch {
            $validationLabel.Text = $_.Exception.Message
            $apiKeyBox.SelectAll()
            $apiKeyBox.Focus()
            return
        }

        $saveButton.Enabled = $false
        $pasteButton.Enabled = $false
        $toggleButton.Enabled = $false
        $form.UseWaitCursor = $true
        [System.Windows.Forms.Application]::DoEvents()
        $failureMessage = $null
        try {
            $result = & $ConfigureAction $ConfigPath $normalized $CodexExecutable
            $apiKeyBox.Clear()
            $state = if ($result.Changed) { 'updated' } else { 'already current' }
            $message = "TVCMall MCP configuration is $state.`r`n`r`nConfig: $($result.ConfigPath)"
            if ($null -ne $result.BackupPath) {
                $message += "`r`nBackup: $($result.BackupPath)"
            }
            $message += "`r`n`r`nRestart Codex or start a new session before using the TVCMall tools."
            & $MessageAction $message 'TVCMall MCP configured' ([System.Windows.Forms.MessageBoxIcon]::Information)
            $form.Tag = $result
            $form.DialogResult = [System.Windows.Forms.DialogResult]::OK
            $form.Close()
        }
        catch {
            $failureMessage = $_.Exception.Message
            if ($failureMessage.Contains($normalized)) {
                $failureMessage = 'The configuration could not be saved. No API Key was logged.'
            }
            $apiKeyBox.Clear()
        }
        finally {
            $form.UseWaitCursor = $false
            if (-not $form.IsDisposed) {
                $pasteButton.Enabled = $true
                $toggleButton.Enabled = $true
                & $updateState
                if ($null -ne $failureMessage) {
                    $validationLabel.Text = $failureMessage
                    $validationLabel.Focus()
                }
            }
            $normalized = $null
        }
    }).GetNewClosure())
    $form.Add_Shown(({
        # A hidden PowerShell console can mark the process's first window as hidden.
        # Explicitly show the form after its native handle exists.
        [TvcmallSetup.NativeMethods]::ShowWindow($form.Handle, 5) | Out-Null
        $form.Activate()
        [TvcmallSetup.NativeMethods]::SetForegroundWindow($form.Handle) | Out-Null
        $apiKeyBox.Focus()
    }).GetNewClosure())
    $form.Add_FormClosed(({
        $apiKeyBox.Clear()
    }).GetNewClosure())

    return $form
}

function Show-TvcmallSetupDialog {
    [CmdletBinding()]
    param()

    $configPath = Resolve-TvcmallConfigPath
    $form = New-TvcmallSetupForm -ConfigPath $configPath
    try {
        $dialogResult = $form.ShowDialog()
        if ($dialogResult -eq [System.Windows.Forms.DialogResult]::OK) {
            return 0
        }
        return 1
    }
    finally {
        $form.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        exit (Show-TvcmallSetupDialog)
    }
    catch {
        try {
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show(
                'The TVCMall setup dialog could not start. Run it again from a local Windows desktop session.',
                'TVCMall MCP setup',
                [System.Windows.Forms.MessageBoxButtons]::OK,
                [System.Windows.Forms.MessageBoxIcon]::Error
            ) | Out-Null
        }
        catch {
            # There is no safe interactive fallback when the desktop UI is unavailable.
        }
        exit 2
    }
}
