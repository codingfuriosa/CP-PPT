# Zero-install static server for Windows (PowerShell ships with Windows). Serves the folder this file is in.
# Requests are handled in parallel (8 workers) and images/media are cacheable, so pictures load once and then appear instantly.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$port = 4173
$l = New-Object System.Net.HttpListener
$l.Prefixes.Add("http://localhost:$port/")
try { $l.Start() } catch { Write-Host "Could not start on port $port. Is it already running? Close other windows of this and try again."; exit 1 }
Write-Host "Limitless Success is running at http://localhost:$port/  (close this window to stop)"

$handler = {
  param($c, $root)
  $types = @{ '.html'='text/html; charset=utf-8'; '.js'='text/javascript'; '.css'='text/css'; '.json'='application/json'; '.mp4'='video/mp4'; '.webm'='video/webm'; '.jpg'='image/jpeg'; '.jpeg'='image/jpeg'; '.png'='image/png'; '.svg'='image/svg+xml'; '.woff2'='font/woff2'; '.woff'='font/woff'; '.glb'='model/gltf-binary'; '.mp3'='audio/mpeg'; '.wav'='audio/wav'; '.webp'='image/webp' }
  $req = $c.Request; $res = $c.Response
  try {
    $p = [Uri]::UnescapeDataString($req.Url.AbsolutePath).TrimStart('/')
    if ($p -eq '') { $p = 'index.html' }
    $f = [IO.Path]::GetFullPath((Join-Path $root $p))
    if (-not $f.StartsWith($root) -or -not (Test-Path $f -PathType Leaf)) { $res.StatusCode = 404; $res.Close(); return }
    $ext = [IO.Path]::GetExtension($f).ToLower()
    if ($types.ContainsKey($ext)) { $res.ContentType = $types[$ext] } else { $res.ContentType = 'application/octet-stream' }
    $res.AddHeader('Accept-Ranges', 'bytes')
    # The page and code always come fresh; pictures, fonts and media are cached for the session so they show instantly.
    if ($ext -eq '.html' -or $ext -eq '.js' -or $ext -eq '.css') { $res.AddHeader('Cache-Control', 'no-cache') }
    else { $res.AddHeader('Cache-Control', 'public, max-age=86400') }
    $res.AddHeader('Last-Modified', (Get-Item $f).LastWriteTimeUtc.ToString('r'))
    $fs = [IO.File]::OpenRead($f); $size = $fs.Length; $start = 0; $end = $size - 1
    $rg = $req.Headers['Range']
    if ($rg -match 'bytes=(\d*)-(\d*)') {
      if ($matches[1] -ne '') { $start = [int64]$matches[1] }
      if ($matches[2] -ne '') { $end = [int64]$matches[2] }
      $res.StatusCode = 206; $res.AddHeader('Content-Range', "bytes $start-$end/$size")
    }
    $len = $end - $start + 1; $res.ContentLength64 = $len
    [void]$fs.Seek($start, 'Begin')
    $buf = New-Object byte[] 262144; $rem = $len
    while ($rem -gt 0) { $n = $fs.Read($buf, 0, [Math]::Min($buf.Length, $rem)); if ($n -le 0) { break }; $res.OutputStream.Write($buf, 0, $n); $rem -= $n }
    $fs.Close()
  } catch { }
  try { $res.Close() } catch { }
}

$pool = [RunspaceFactory]::CreateRunspacePool(1, 8); $pool.Open()
$jobs = New-Object System.Collections.ArrayList
Start-Process "http://localhost:$port/#/solo"
while ($l.IsListening) {
  $c = $l.GetContext()
  $ps = [PowerShell]::Create(); $ps.RunspacePool = $pool
  [void]$ps.AddScript($handler).AddArgument($c).AddArgument($root)
  [void]$jobs.Add(@{ ps = $ps; h = $ps.BeginInvoke() })
  # tidy up finished workers
  for ($i = $jobs.Count - 1; $i -ge 0; $i--) { $j = $jobs[$i]; if ($j.h.IsCompleted) { try { $j.ps.EndInvoke($j.h) } catch { }; $j.ps.Dispose(); $jobs.RemoveAt($i) } }
}
