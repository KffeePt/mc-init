<#
.SYNOPSIS
  Hermes screenshot helper for Windows child agents.
.DESCRIPTION
  Captures the current primary screen to a PNG file. This helper is intentionally
  dependency-light and safe for user/agent use from PowerShell. It writes under
  Documents\Hermes\Artifacts by default unless -OutputPath is provided.
.SAFETY
  Screenshots may contain private information. Do not send externally unless Xan
  explicitly requested it or the current task scope clearly requires it.
#>
param(
  [string]$OutputPath
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
if (-not $OutputPath -or $OutputPath.Trim() -eq '') {
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $dir = Join-Path $env:USERPROFILE 'Documents\Hermes\Artifacts\Screenshots'
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $OutputPath = Join-Path $dir "screenshot-$stamp.png"
}
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
try {
  $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
  $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
  $item = Get-Item -LiteralPath $OutputPath
  [pscustomobject]@{ ok = $true; path = $item.FullName; bytes = $item.Length; width = $bounds.Width; height = $bounds.Height } | ConvertTo-Json -Compress
}
finally {
  $graphics.Dispose()
  $bitmap.Dispose()
}
