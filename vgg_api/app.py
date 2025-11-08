from flask import Flask, request, jsonify, send_from_directory, render_template_string, abort
from pathlib import Path
import mimetypes, time, json

# ---------- PATHS ----------
BASE_DIR       = Path(__file__).resolve().parent
DATASETS_ROOT  = Path("/home/ubuntu/datasets").resolve()       # your images, class folders inside
VIA_DIR        = (BASE_DIR / "via-2.0.12").resolve()           # unzipped via-2.0.12 here
ANNOT_ROOT     = (BASE_DIR / "annotations").resolve()          # saved VIA projects here
# ---------------------------

ANNOT_ROOT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)  # we’ll serve VIA and images with explicit routes

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

def _safe_folder(name: str) -> Path:
    p = (DATASETS_ROOT / name).resolve()
    if not p.is_dir() or (p != DATASETS_ROOT and DATASETS_ROOT not in p.parents):
        abort(404)
    return p

def _list_images(folder: Path):
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS])

# -------------------- ROUTES --------------------

@app.route("/")
def index():
    if not (VIA_DIR / "via.html").exists():
        return "via-2.0.12/via.html not found. Unzip into vgg_api/via-2.0.12/", 500
    classes = sorted([p.name for p in DATASETS_ROOT.iterdir() if p.is_dir()])
    counts = {n: len(_list_images(DATASETS_ROOT / n)) for n in classes}
    return render_template_string("""
<!doctype html>
<title>Datasets</title>
<style>
  body{font:14px/1.4 system-ui, sans-serif; max-width:960px; margin:32px auto;}
  a.btn{display:inline-block;padding:6px 10px;border:1px solid #ccc;border-radius:8px;text-decoration:none}
  table{border-collapse:collapse;width:100%}
  th,td{padding:8px 10px;border-bottom:1px solid #eee;text-align:left}
  code{background:#f6f6f6;padding:1px 4px;border-radius:4px}
</style>
<h2>Datasets under <code>{{root}}</code></h2>
<table>
  <tr><th>Folder</th><th>Images</th><th></th></tr>
  {% for name in classes %}
  <tr>
    <td><code>{{name}}</code></td>
    <td>{{counts[name]}}</td>
    <td><a class="btn" href="/annotate/{{name}}">Open in VIA</a></td>
  </tr>
  {% endfor %}
</table>
""", root=str(DATASETS_ROOT), classes=classes, counts=counts)

@app.route("/annotate/<folder>")
def annotate(folder):
    folder_path = _safe_folder(folder)
    return render_template_string("""
<!doctype html>
<title>Annotate: {{folder}}</title>
<style>
  body{margin:0;font:14px system-ui, sans-serif}
  header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:10px 12px;z-index:2}
  #viaframe{width:100vw;height:calc(100vh - 54px);border:0}
  .btn{padding:6px 10px;border:1px solid #ccc;border-radius:8px;background:#f8f8f8;cursor:pointer}
  .status{margin-left:10px;color:#666}
</style>
<header>
  <strong>Folder:</strong> <code>{{folder}}</code>
  <button class="btn" id="saveBtn">Save to Server</button>
  <label style="margin-left:10px;"><input type="checkbox" id="autosaveToggle"> Auto-save (60s)</label>
  <span class="status" id="status"></span>
</header>
<iframe id="viaframe" src="/via/via.html"></iframe>

<script>
const folder = {{ folder|tojson }};
const statusEl = document.getElementById('status');
const frame = document.getElementById('viaframe');

async function fetchImages() {
  const r = await fetch(`/api/list-images?folder=${encodeURIComponent(folder)}`);
  if (!r.ok) throw new Error("list-images failed");
  return (await r.json()).images;
}

function addImagesToVia(w, urls) {
  // Add remote-image URLs to VIA, then show first image.
  // (VIA allows adding URLs programmatically.)
  urls.forEach(u => w.project_file_add_url(u));
  w.update_img_fn_list();
  if (w._via_image_id_list && w._via_image_id_list.length) w._via_show_img(0);
}

async function init() {
  const urls = await fetchImages();
  frame.addEventListener('load', () => {
    try {
      const w = frame.contentWindow;
      addImagesToVia(w, urls);
      statusEl.textContent = `Loaded ${urls.length} images`;
    } catch (e) {
      console.error(e); statusEl.textContent = 'Failed to init VIA';
    }
  }, { once: true });
}
init().catch(e => { console.error(e); statusEl.textContent = 'Init failed'; });

function collectViaProject() {
  const w = frame.contentWindow;
  return {
    _via_settings: w._via_settings,
    _via_img_metadata: w._via_img_metadata,
    _via_attributes: w._via_attributes,
    _via_data_format_version: w._via_data_format_version,
    _via_image_id_list: w._via_image_id_list
  };
}

async function saveToServer() {
  try {
    const project = collectViaProject();
    const r = await fetch('/api/save', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ folder, project })
    });
    if (!r.ok) throw new Error('Save failed');
    const j = await r.json();
    statusEl.textContent = `Saved: ${j.path}`;
  } catch (e) {
    console.error(e); statusEl.textContent = 'Save error';
  }
}

document.getElementById('saveBtn').addEventListener('click', saveToServer);

let autosaveTimer = null;
document.getElementById('autosaveToggle').addEventListener('change', (e) => {
  if (e.target.checked) { autosaveTimer = setInterval(saveToServer, 60000); statusEl.textContent = 'Auto-save ON'; }
  else { clearInterval(autosaveTimer); autosaveTimer = null; statusEl.textContent = 'Auto-save OFF'; }
});

document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); saveToServer(); }
});
</script>
""", folder=folder_path.name)

@app.route("/api/list-images")
def list_images():
    folder = request.args.get("folder", "")
    folder_path = _safe_folder(folder)
    images = _list_images(folder_path)
    urls = [f"/files/{folder}/{p.name}" for p in images]
    return jsonify({"folder": folder, "count": len(urls), "images": urls})

@app.route("/files/<folder>/<path:filename>")
def serve_image(folder, filename):
    folder_path = _safe_folder(folder)
    file_path = (folder_path / filename).resolve()
    if not file_path.exists() or DATASETS_ROOT not in file_path.parents:
        abort(404)
    mt, _ = mimetypes.guess_type(str(file_path))
    return send_from_directory(folder_path, filename, mimetype=mt or "application/octet-stream")

@app.route("/via/<path:filename>")
def serve_via(filename):
    # Serve the unmodified VIA 2.0.12 files (single-page app)
    return send_from_directory(VIA_DIR, filename)

@app.route("/api/save", methods=["POST"])
def save():
    data = request.get_json(force=True, silent=False) or {}
    folder = data.get("folder")
    project = data.get("project")
    if not folder or not isinstance(project, dict):
        abort(400)
    _ = _safe_folder(folder)  # validate
    ts = time.strftime("%Y%m%d-%H%M%S")
    latest  = (ANNOT_ROOT / f"{folder}.via2.json")
    version = (ANNOT_ROOT / "revisions" / folder / f"{ts}.via2.json")
    version.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    version.write_text(json.dumps(project, ensure_ascii=False, indent=2))
    return jsonify({"ok": True, "path": str(latest)})

@app.route("/healthz")
def health():
    return "ok"

# -------------------- MAIN --------------------
if __name__ == "__main__":
    # For LAN access in a lab: open on 0.0.0.0
    app.run(host="0.0.0.0", port=5010, debug=True)
