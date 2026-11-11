# Zero-install static server for Windows (PowerShell ships with Windows). Serves the folder this file is in.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$port = 4173
$types = @{ '.html'='text/html; charset=utf-8'; '.js'='text/javascript'; '.css'='text/css'; '.json'='application/json'; '.mp4'='video/mp4'; '.webm'='video/webm'; '.jpg'='image/jpeg'; '.jpeg'='image/jpeg'; '.png'='image/png'; '.svg'='image/svg+xml'; '.woff2'='font/woff2'; '.woff'='font/woff'; '.glb'='model/gltf-binary'; '.mp3'='audio/mpeg'; '.wav'='audio/wav'; '.webp'='image/webp' }
$l = New-Object System.Net.HttpListener
$l.Prefixes.Add("http://localhost:$port/")
try { $l.Start() } catch { Write-Host "Could not start on port $port. Is it already running? Close other windows of this and try again."; exit 1 }
Write-Host "Limitless Success is running at http://localhost:$port/  (close this window to stop)"
Start-Process "http://localhost:$port/#/solo"
while ($l.IsListening) {
  $c = $l.GetContext(); $req = $c.Request; $res = $c.Response
  try {
    $p = [Uri]::UnescapeDataString($req.Url.AbsolutePath).TrimStart('/')
    if ($p -eq '') { $p = 'index.html' }
    $f = [IO.Path]::GetFullPath((Join-Path $root $p))
    if (-not $f.StartsWith($root) -or -not (Test-Path $f -PathType Leaf)) { $res.StatusCode = 404; $res.Close(); continue }
    $ext = [IO.Path]::GetExtension($f).ToLower()
    if ($types.ContainsKey($ext)) { $res.ContentType = $types[$ext] } else { $res.ContentType = 'application/octet-stream' }
    $res.AddHeader('Accept-Ranges', 'bytes'); $res.AddHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
    $fs = [IO.File]::OpenRead($f); $size = $fs.Length; $start = 0; $end = $size - 1
    $rg = $req.Headers['Range']
    if ($rg -match 'bytes=(\d*)-(\d*)') {
      if ($matches[1] -ne '') { $start = [int64]$matches[1] }
      if ($matches[2] -ne '') { $end = [int64]$matches[2] }
      $res.StatusCode = 206; $res.AddHeader('Content-Range', "bytes $start-$end/$size")
    }
    $len = $end - $start + 1; $res.ContentLength64 = $len
    [void]$fs.Seek($start, 'Begin')
    $buf = New-Object byte[] 65536; $rem = $len
    while ($rem -gt 0) { $n = $fs.Read($buf, 0, [Math]::Min($buf.Length, $rem)); if ($n -le 0) { break }; $res.OutputStream.Write($buf, 0, $n); $rem -= $n }
    $fs.Close()
  } catch { }
  try { $res.Close() } catch { }
}
