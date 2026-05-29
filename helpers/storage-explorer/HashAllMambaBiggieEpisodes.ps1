<#
Purpose: Full SHA-256 hash verification of ALL matched episodes between MAMBA and BIGGIE Archived.
Date: 2026-05-26
Inputs: F:\Shows, D:\Archived Shows, D:\Archied Shows
Side effects: Read-only. Hashes every matched episode on both drives. No deletion.
Output: CSV/JSON/MD report in artifact dir.
Duration: Hours. ~5,376 episodes × 2 hashes. Background only.
#>
param(
  [string]$MambaRoot = "F:\Shows",
  [string[]]$ArchivedRoots = @("D:\Archived Shows", "D:\Archied Shows"),
  [string]$OutDir = "C:\Users\santi\Documents\Hermes\Artifacts\2026-05-26\10-30-00\Mamba Biggie Full Hash Verification"
)
$ErrorActionPreference = 'Continue'
$start = Get-Date
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$progressFile = Join-Path $OutDir "progress.json"
$resultsFile = Join-Path $OutDir "Hash Results.csv"
$mismatchFile = Join-Path $OutDir "Hash Mismatches.csv"

function Write-ProgressData($data) {
  $data | ConvertTo-Json -Depth 4 -Compress | Set-Content -LiteralPath $progressFile -Encoding UTF8
}

function Get-SHA256($path) {
  try { return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() }
  catch { return "ERROR:$($_.Exception.Message)" }
}

# Build episode map: show -> episodeKey -> {MambaPath, ArchivedPath}
Write-ProgressData @{ phase="scanning"; status="Building episode maps..." }
$mambaShows = @{}
Get-ChildItem -LiteralPath $MambaRoot -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
  $showName = $_.Name
  if ($showName -eq 'Plex Versions') { return }
  $eps = @{}
  Get-ChildItem -LiteralPath $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -match '\.(mkv|mp4|avi|m4v|mov|wmv|webm|ts|m2ts)$' } |
    ForEach-Object { $eps[$_.Name.ToLowerInvariant()] = $_.FullName }
  $mambaShows[$showName] = $eps
}

$archivedShows = @{}
foreach ($root in $ArchivedRoots) {
  if (-not (Test-Path $root)) { continue }
  Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $showName = $_.Name
    $eps = @{}
    Get-ChildItem -LiteralPath $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Extension -match '\.(mkv|mp4|avi|m4v|mov|wmv|webm|ts|m2ts)$' } |
      ForEach-Object { $eps[$_.Name.ToLowerInvariant()] = $_.FullName }
    if (-not $archivedShows.ContainsKey($showName)) { $archivedShows[$showName] = $eps }
    else { foreach ($k in $eps.Keys) { $archivedShows[$showName][$k] = $eps[$k] } }
  }
}

# Build matched pairs
$matchedPairs = New-Object System.Collections.Generic.List[object]
$commonShows = $mambaShows.Keys | Where-Object { $_ -in $archivedShows.Keys } | Sort-Object
foreach ($show in $commonShows) {
  $mEps = $mambaShows[$show]
  $aEps = $archivedShows[$show]
  foreach ($key in $mEps.Keys) {
    if ($aEps.ContainsKey($key)) {
      # verify size match before hashing
      $mSize = (Get-Item -LiteralPath $mEps[$key] -Force).Length
      $aSize = (Get-Item -LiteralPath $aEps[$key] -Force).Length
      $matchedPairs.Add([pscustomobject]@{
        Show = $show
        EpisodeKey = $key
        MambaPath = $mEps[$key]
        ArchivedPath = $aEps[$key]
        MambaSize = [int64]$mSize
        ArchivedSize = [int64]$aSize
        SizeMatch = ($mSize -eq $aSize)
      })
    }
  }
}

$totalPairs = $matchedPairs.Count
$totalGiB = [math]::Round(($matchedPairs | Measure-Object MambaSize -Sum).Sum / 1GB, 2)

Write-ProgressData @{
  phase = "hashing"
  status = "Starting"
  totalPairs = $totalPairs
  totalGiB = $totalGiB
  started = $start.ToString('s')
}

# Hash all pairs
$results = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
$mismatches = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
$done = 0
$matchCount = 0
$mismatchCount = 0
$errorCount = 0
$hashGiB = [double]0

# Use runspace pool for parallel hashing
$maxThreads = 4
$runspacePool = [runspacefactory]::CreateRunspacePool(1, $maxThreads)
$runspacePool.Open()
$jobs = @()

$scriptBlock = {
  param($pair)
  try {
    $mHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $pair.MambaPath).Hash.ToLowerInvariant()
    $aHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $pair.ArchivedPath).Hash.ToLowerInvariant()
    [pscustomobject]@{
      Show = $pair.Show
      EpisodeKey = $pair.EpisodeKey
      MambaPath = $pair.MambaPath
      ArchivedPath = $pair.ArchivedPath
      MambaSize = $pair.MambaSize
      ArchivedSize = $pair.ArchivedSize
      MambaSHA256 = $mHash
      ArchivedSHA256 = $aHash
      Match = ($mHash -eq $aHash)
      Error = $null
    }
  } catch {
    [pscustomobject]@{
      Show = $pair.Show
      EpisodeKey = $pair.EpisodeKey
      MambaPath = $pair.MambaPath
      ArchivedPath = $pair.ArchivedPath
      MambaSize = $pair.MambaSize
      ArchivedSize = $pair.ArchivedSize
      MambaSHA256 = $null
      ArchivedSHA256 = $null
      Match = $false
      Error = $_.Exception.Message
    }
  }
}

$totalBatches = [math]::Ceiling($totalPairs / $maxThreads)
$batchNum = 0

for ($i = 0; $i -lt $totalPairs; $i += $maxThreads) {
  $batchNum++
  $batchEnd = [math]::Min($i + $maxThreads - 1, $totalPairs - 1)
  $batch = $matchedPairs[$i..$batchEnd]
  
  $batchJobs = @()
  foreach ($pair in $batch) {
    $ps = [powershell]::Create().AddScript($scriptBlock).AddArgument($pair)
    $ps.RunspacePool = $runspacePool
    $batchJobs += [pscustomobject]@{ PowerShell = $ps; Handle = $ps.BeginInvoke() }
  }
  
  # Wait for batch
  foreach ($job in $batchJobs) {
    $result = $job.PowerShell.EndInvoke($job.Handle)
    $job.PowerShell.Dispose()
    [void]$results.Add($result)
    $done++
    $hashGiB += (($result.MambaSize + $result.ArchivedSize) / 1GB)
    if ($result.Match -and -not $result.Error) { $matchCount++ }
    elseif ($result.Error) { $errorCount++; [void]$mismatches.Add($result) }
    else { $mismatchCount++; [void]$mismatches.Add($result) }
  }
  
  # Write intermediate results every batch
  if ($done -gt 0) {
    $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    $rate = if ($elapsed -gt 0) { [math]::Round($done / $elapsed, 2) } else { 0 }
    $eta = if ($rate -gt 0) { [math]::Round(($totalPairs - $done) / $rate, 0) } else { "unknown" }
    $tempResults = @($results) | Sort-Object Show, EpisodeKey
    $tempMismatches = @($mismatches)
    $tempResults | Export-Csv -NoTypeInformation -LiteralPath $resultsFile -Encoding UTF8 -Force
    if ($tempMismatches.Count -gt 0) {
      $tempMismatches | Export-Csv -NoTypeInformation -LiteralPath $mismatchFile -Encoding UTF8 -Force
    }
    Write-ProgressData @{
      phase = "hashing"
      status = "Progress"
      done = $done
      total = $totalPairs
      match = $matchCount
      mismatch = $mismatchCount
      error = $errorCount
      hashGiB = [math]::Round($hashGiB, 2)
      elapsed = $elapsed
      rate = "$rate eps/sec"
      etaSeconds = $eta
    }
  }
}

$runspacePool.Close()
$runspacePool.Dispose()

# Final results
$elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
$finalResults = @($results) | Sort-Object Show, EpisodeKey
$finalMismatches = @($mismatches)
$finalResults | Export-Csv -NoTypeInformation -LiteralPath $resultsFile -Encoding UTF8
if ($finalMismatches.Count -gt 0) {
  $finalMismatches | Export-Csv -NoTypeInformation -LiteralPath $mismatchFile -Encoding UTF8
}

$summary = [pscustomobject]@{
  Started = $start.ToString('s')
  Completed = (Get-Date).ToString('s')
  ElapsedSeconds = $elapsed
  TotalEpisodes = $totalPairs
  TotalDataGiB = $totalGiB
  Match = $matchCount
  Mismatch = $mismatchCount
  Error = $errorCount
  MismatchDetails = @($finalMismatches | Select-Object Show, EpisodeKey, MambaPath, ArchivedPath, MambaSHA256, ArchivedSHA256, Error | ForEach-Object { $_ })
}
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutDir "Hash Summary.json") -Encoding UTF8

Write-ProgressData @{
  phase = "done"
  done = $totalPairs
  total = $totalPairs
  match = $matchCount
  mismatch = $mismatchCount
  error = $errorCount
  elapsed = $elapsed
}
$summary | ConvertTo-Json -Depth 6
