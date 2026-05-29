<#
Purpose: Episode-level comparison between MAMBA (F:\Shows) and BIGGIE Archived (D:\Archived Shows + D:\Archied Shows).
Date: 2026-05-26
Inputs: F:\Shows, D:\Archived Shows, D:\Archied Shows
Side effects: Read-only. Hashes only size-mismatched files. No deletion.
Output: CSVs, JSON summary in artifact dir.
Safety: No writes to source drives.
#>
param(
  [string]$MambaRoot = "F:\Shows",
  [string[]]$ArchivedRoots = @("D:\Archived Shows", "D:\Archied Shows"),
  [string]$OutDir = "C:\Users\santi\Documents\Hermes\Artifacts\2026-05-26\09-10-00\Mamba Biggie Episode Hash Comparison",
  [int]$MaxHashPerShow = 20
)
$ErrorActionPreference = 'Continue'
$start = Get-Date
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Get-Episodes($root) {
  if (-not (Test-Path $root)) { return @{} }
  $shows = @{}
  Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $showName = $_.Name
    if ($showName -eq 'Plex Versions') { return }
    $eps = Get-ChildItem -LiteralPath $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Extension -match '\.(mkv|mp4|avi|m4v|mov|wmv|webm|ts|m2ts)$' }
    $epsByName = @{}
    foreach ($e in $eps) {
      $key = $e.Name.ToLowerInvariant()
      if (-not $epsByName.ContainsKey($key)) {
        $epsByName[$key] = [pscustomobject]@{
          Name = $e.Name
          FullPath = $e.FullName
          Size = [int64]$e.Length
          LastWriteTime = $e.LastWriteTime
        }
      }
    }
    $shows[$showName] = $epsByName
  }
  return $shows
}

function Get-SHA256($path) {
  try { return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() }
  catch { return $null }
}

Write-Progress -Activity "MAMBA→BIGGIE episode comparison" -Status "Scanning MAMBA episodes..." -PercentComplete 0
$mamba = Get-Episodes $MambaRoot

Write-Progress -Activity "MAMBA→BIGGIE episode comparison" -Status "Scanning Archived episodes..." -PercentComplete 20
$archived = @{}
foreach ($root in $ArchivedRoots) {
  $a = Get-Episodes $root
  foreach ($k in $a.Keys) { $archived[$k] = $a[$k] }
}

# Find common shows
$mambaNames = [string[]]$mamba.Keys
$archivedNames = [string[]]$archived.Keys
$commonShows = $mambaNames | Where-Object { $_ -in $archivedNames }
$mambaOnly = $mambaNames | Where-Object { $_ -notin $archivedNames }
$archivedOnly = $archivedNames | Where-Object { $_ -notin $mambaNames }

Write-Progress -Activity "MAMBA→BIGGIE episode comparison" -Status "Comparing $($commonShows.Count) common shows..." -PercentComplete 30

$results = @{}
$showRows = New-Object System.Collections.Generic.List[object]
$mismatchRows = New-Object System.Collections.Generic.List[object]
$hashRows = New-Object System.Collections.Generic.List[object]
$totalDone = 0
$totalShows = $commonShows.Count

foreach ($show in ($commonShows | Sort-Object)) {
  $totalDone++
  $pct = 30 + [math]::Floor(($totalDone / $totalShows) * 55)
  Write-Progress -Activity "MAMBA→BIGGIE episode comparison" -Status "Show $totalDone/$totalShows : $show" -PercentComplete $pct

  $mEps = $mamba[$show]
  $aEps = $archived[$show]
  $mNames = [string[]]$mEps.Keys
  $aNames = [string[]]$aEps.Keys

  $matched = 0; $missingArchived = 0; $missingMamba = 0
  $sizeMatch = 0; $sizeMismatch = 0; $hashChecked = 0; $hashMatch = 0; $hashMismatch = 0; $hashErrors = 0

  foreach ($n in $mNames) {
    if ($n -in $aNames) {
      $matched++
      $mSize = $mEps[$n].Size
      $aSize = $aEps[$n].Size
      if ($mSize -eq $aSize) {
        $sizeMatch++
      } else {
        $sizeMismatch++
        $row = [pscustomobject]@{
          Show = $show
          Episode = $mEps[$n].Name
          MambaPath = $mEps[$n].FullPath
          ArchivedPath = $aEps[$n].FullPath
          MambaSize = $mSize
          ArchivedSize = $aSize
          SizeDeltaBytes = $mSize - $aSize
          Status = "size_mismatch"
        }
        # Hash both if within limit
        if ($hashChecked -lt $MaxHashPerShow) {
          $mHash = Get-SHA256 $mEps[$n].FullPath
          $aHash = Get-SHA256 $aEps[$n].FullPath
          $hashChecked++
          if ($mHash -and $aHash) {
            $row | Add-Member -NotePropertyName MambaSHA256 -NotePropertyValue $mHash
            $row | Add-Member -NotePropertyName ArchivedSHA256 -NotePropertyValue $aHash
            if ($mHash -eq $aHash) {
              $row.Status = "size_mismatch_but_hash_match"
              $hashMatch++
            } else {
              $row.Status = "hash_mismatch"
              $hashMismatch++
            }
          } else {
            $hashErrors++
            $row | Add-Member -NotePropertyName MambaSHA256 -NotePropertyValue $mHash
            $row | Add-Member -NotePropertyName ArchivedSHA256 -NotePropertyValue $aHash
            $row.Status = "hash_error"
          }
          $hashRows.Add($row)
        }
        $mismatchRows.Add($row)
      }
    } else {
      $missingArchived++
      $mismatchRows.Add([pscustomobject]@{
        Show = $show; Episode = $mEps[$n].Name; MambaPath = $mEps[$n].FullPath
        ArchivedPath = $null; MambaSize = $mEps[$n].Size; ArchivedSize = $null
        SizeDeltaBytes = $null; Status = "missing_from_archived"
      })
    }
  }
  # check archived-only episodes
  foreach ($n in $aNames) {
    if ($n -notin $mNames) {
      $missingMamba++
      $mismatchRows.Add([pscustomobject]@{
        Show = $show; Episode = $aEps[$n].Name; MambaPath = $null
        ArchivedPath = $aEps[$n].FullPath; MambaSize = $null; ArchivedSize = $aEps[$n].Size
        SizeDeltaBytes = $null; Status = "missing_from_mamba"
      })
    }
  }

  $r = [pscustomobject]@{
    Show = $show
    MambaEpisodes = $mEps.Count
    ArchivedEpisodes = $aEps.Count
    Matched = $matched
    SizeMatch = $sizeMatch
    SizeMismatch = $sizeMismatch
    HashChecked = $hashChecked
    HashMatch = $hashMatch
    HashMismatch = $hashMismatch
    HashErrors = $hashErrors
    MissingFromArchived = $missingArchived
    MissingFromMamba = $missingMamba
  }
  $results[$show] = $r
  $showRows.Add($r)
}

Write-Progress -Activity "MAMBA→BIGGIE episode comparison" -Status "Writing outputs..." -PercentComplete 95

# Totals
$totalMatched = ($showRows | Measure-Object Matched -Sum).Sum
$totalSizeMatch = ($showRows | Measure-Object SizeMatch -Sum).Sum
$totalSizeMismatch = ($showRows | Measure-Object SizeMismatch -Sum).Sum
$totalHashChecked = ($showRows | Measure-Object HashChecked -Sum).Sum
$totalHashMatch = ($showRows | Measure-Object HashMatch -Sum).Sum
$totalHashMismatch = ($showRows | Measure-Object HashMismatch -Sum).Sum
$totalMissingArchived = ($showRows | Measure-Object MissingFromArchived -Sum).Sum
$totalMissingMamba = ($showRows | Measure-Object MissingFromMamba -Sum).Sum

$summary = [pscustomobject]@{
    Started = $start.ToString('s')
    ElapsedSeconds = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    MambaRoot = $MambaRoot
    ArchivedRoots = $ArchivedRoots
    TotalCommonShows = $commonShows.Count
    MambaOnlyShows = $mambaOnly
    ArchivedOnlyShows = $archivedOnly
    TotalEpisodesCompared = $totalMatched
    SizeMatch = $totalSizeMatch
    SizeMismatch = $totalSizeMismatch
    HashChecked = $totalHashChecked
    HashMatch = $totalHashMatch
    HashMismatch = $totalHashMismatch
    MissingFromArchived = $totalMissingArchived
    MissingFromMamba = $totalMissingMamba
}

$showRows | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $OutDir "Show Comparison.csv") -Encoding UTF8
$mismatchRows | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $OutDir "Episode Mismatches.csv") -Encoding UTF8
if ($hashRows.Count -gt 0) {
    $hashRows | Export-Csv -NoTypeInformation -LiteralPath (Join-Path $OutDir "Hash Results.csv") -Encoding UTF8
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutDir "Episode Comparison Summary.json") -Encoding UTF8
Write-Progress -Activity "MAMBA→BIGGIE episode comparison" -Completed

# Output summary to stdout
$summary | ConvertTo-Json -Depth 5
