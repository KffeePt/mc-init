<#
Purpose: Execute high-confidence BIGGIE cleanup targets and prepare for duplicate hash analysis.
Date: 2026-05-26
Inputs:
  - D:\Movies\Plex Versions
  - D:\$RECYCLE.BIN
Side effects:
  - Deletes Plex-generated version files/folders if present.
  - Clears D: recycle bin payloads by removing contents under D:\$RECYCLE.BIN.
Safety notes:
  - Guarded to D:\ exact targets only.
  - Does not touch D:\Shows, D:\Archived Shows, D:\Archied Shows, D:\Movies originals, D:\ISO, D:\VMs, D:\Cracked_Programs, or D:\Buffer & Backups.
  - Writes JSON/CSV results to artifact directory.
#>
param(
  [Parameter(Mandatory=$true)][string]$ArtifactDir
)
$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null

function Get-TreeStats {
  param([string]$Path)
  $result = [ordered]@{ Path=$Path; Exists=(Test-Path -LiteralPath $Path); Files=0; Dirs=0; Bytes=0 }
  if (-not $result.Exists) { return [pscustomobject]$result }
  try {
    $items = Get-ChildItem -LiteralPath $Path -Force -Recurse -ErrorAction SilentlyContinue
    foreach ($i in $items) {
      if ($i.PSIsContainer) { $result.Dirs++ } else { $result.Files++; $result.Bytes += [int64]$i.Length }
    }
    if ((Get-Item -LiteralPath $Path -Force).PSIsContainer -eq $false) { $result.Files=1; $result.Bytes=(Get-Item -LiteralPath $Path -Force).Length }
  } catch { $result.Error = $_.Exception.Message }
  [pscustomobject]$result
}

$beforeDrive = Get-PSDrive D | Select-Object Name,Free,Used,@{n='Total';e={$_.Free+$_.Used}}
$targets = @(
  [pscustomobject]@{ Name='Plex generated versions'; Path='D:\Movies\Plex Versions'; Mode='RemoveDirectoryContentsAndRoot'; Guard='D:\Movies\Plex Versions' },
  [pscustomobject]@{ Name='D recycle bin contents'; Path='D:\$RECYCLE.BIN'; Mode='RemoveChildrenOnly'; Guard='D:\$RECYCLE.BIN' }
)
$results = New-Object System.Collections.Generic.List[object]
foreach ($t in $targets) {
  $before = Get-TreeStats $t.Path
  $status = 'not_found'
  $errorText = $null
  $deletedBytes = [int64]$before.Bytes
  try {
    if ($before.Exists) {
      $resolved = (Resolve-Path -LiteralPath $t.Path -ErrorAction Stop).Path
      if ($resolved.TrimEnd('\') -ne $t.Guard.TrimEnd('\')) { throw "Guard mismatch: $resolved != $($t.Guard)" }
      if ($t.Mode -eq 'RemoveDirectoryContentsAndRoot') {
        Remove-Item -LiteralPath $t.Path -Recurse -Force -ErrorAction Stop
      } elseif ($t.Mode -eq 'RemoveChildrenOnly') {
        Get-ChildItem -LiteralPath $t.Path -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction Stop
      }
      $status = 'deleted'
    }
  } catch {
    $status = 'failed'
    $errorText = $_.Exception.Message
  }
  Start-Sleep -Milliseconds 100
  $after = Get-TreeStats $t.Path
  $results.Add([pscustomobject]@{
    Name=$t.Name; Path=$t.Path; Mode=$t.Mode; Status=$status; Error=$errorText;
    BeforeExists=$before.Exists; BeforeFiles=$before.Files; BeforeDirs=$before.Dirs; BeforeBytes=[int64]$before.Bytes;
    AfterExists=$after.Exists; AfterFiles=$after.Files; AfterDirs=$after.Dirs; AfterBytes=[int64]$after.Bytes;
    DeletedBytes= if ($status -eq 'deleted') { [int64]$deletedBytes } else { 0 }
  })
}
$afterDrive = Get-PSDrive D | Select-Object Name,Free,Used,@{n='Total';e={$_.Free+$_.Used}}
$summary = [pscustomobject]@{
  Timestamp=(Get-Date).ToString('s')
  Targets=$results
  DriveBefore=$beforeDrive
  DriveAfter=$afterDrive
  FreeDeltaBytes=[int64]($afterDrive.Free - $beforeDrive.Free)
  AccountedDeletedBytes=[int64](($results | Measure-Object DeletedBytes -Sum).Sum)
}
$results | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $ArtifactDir 'Small Cleanup Results.csv') -Encoding UTF8
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ArtifactDir 'Small Cleanup Summary.json') -Encoding UTF8
$summary | ConvertTo-Json -Depth 6
