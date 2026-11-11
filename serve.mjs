// Zero-dependency static server for offline presentation.  Usage: npm run build && npm run serve
// Supports HTTP Range requests (required for <video> seeking) and serves ./dist.
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
// works both from the project (serves ../dist) and from inside the offline folder (serves itself)
const root = fs.existsSync(path.join(here, 'index.html')) ? here : path.resolve(here, '..', 'dist')
const port = Number(process.env.PORT || 4173)
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.mp4': 'video/mp4', '.webm': 'video/webm', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff', '.glb': 'model/gltf-binary', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.webp': 'image/webp' }

http.createServer((req, res) => {
  const url = decodeURIComponent((req.url || '/').split('?')[0])
  let file = path.join(root, url === '/' ? 'index.html' : url)
  if (!file.startsWith(root)) { res.writeHead(403).end(); return }
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404).end('Not found'); return }
  const size = fs.statSync(file).size
  const type = types[path.extname(file).toLowerCase()] || 'application/octet-stream'
  const range = req.headers.range
  if (range) {
    const [s, e] = range.replace(/bytes=/, '').split('-')
    const start = parseInt(s, 10); const end = e ? parseInt(e, 10) : size - 1
    res.writeHead(206, { 'Content-Range': `bytes ${start}-${end}/${size}`, 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1, 'Content-Type': type })
    fs.createReadStream(file, { start, end }).pipe(res)
  } else {
    res.writeHead(200, { 'Content-Length': size, 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-cache' })
    fs.createReadStream(file).pipe(res)
  }
}).listen(port, '0.0.0.0', () => console.log(`Limitless Success serving ./dist on http://localhost:${port}`))
