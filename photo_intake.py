"""Camera-first job intake — photo → AI extracts vehicle info → pre-filled job card."""
import os
import json
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()


@router.post("/api/photo/intake")
async def photo_intake(r: Request):
    """Analyse a photo and extract vehicle info for a new job."""
    d = await r.json()
    image_b64 = (d.get("image_base64") or "").strip()
    notes = (d.get("notes") or "").strip()

    if not image_b64:
        raise HTTPException(400, "image_base64 required")
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]
    if len(image_b64) > 7000000:
        raise HTTPException(413, "Image too large")

    if not OPENAI_KEY:
        raise HTTPException(503, "AI not configured")

    prompt = (
        "You are an expert at reading vehicle information from photos. "
        "Look at this image and extract any vehicle details you can see. "
        "It could be a VIN sticker (door jamb / windscreen), a license plate, "
        "a dashboard, an odometer, an engine bay, or a document.\n\n"
        "Return ONLY a JSON object with these fields (use empty string if not visible):\n"
        "{\n"
        '  "vin": "17-character VIN if visible",\n'
        '  "registration": "license plate number (uppercase, no spaces)",\n'
        '  "make": "manufacturer name (Toyota, VW, Ford, etc.)",\n'
        '  "model": "model name (Hilux, Polo, Ranger, etc.)",\n'
        '  "year": "year if visible as a number, else empty",\n'
        '  "km": "odometer reading as a number if visible, else empty",\n'
        '  "colour": "colour if visible",\n'
        '  "vehicle_type": "truck / bakkie / car / bus / tractor / motorcycle / generator / other",\n'
        '  "confidence": "high / medium / low",\n'
        '  "notes": "any other useful observations (damage, warning lights, etc.)"\n'
        "}\n\n"
        "Rules:\n"
        "- Only report what is actually visible. Do not guess.\n"
        "- For registration, remove spaces and hyphens, use uppercase.\n"
        "- For year, prefer the decade that best matches the model if unclear.\n"
        "- Extra notes: " + (notes or "none")
    )

    try:
        import openai
        c = openai.OpenAI(api_key=OPENAI_KEY, timeout=60.0)
        resp = c.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "high"
                    }},
                ]
            }],
            max_tokens=800,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"success": False, "error": f"AI error: {e}"}

    # Normalise
    vin = (data.get("vin") or "").strip().upper()
    if len(vin) != 17:
        vin = ""
    reg = (data.get("registration") or "").strip().upper().replace(" ", "").replace("-", "")
    km_raw = str(data.get("km") or "").strip()
    km = 0
    try:
        km = int("".join(ch for ch in km_raw if ch.isdigit()) or 0)
    except Exception:
        km = 0

    return {
        "success": True,
        "vin": vin,
        "registration": reg,
        "make": (data.get("make") or "").strip(),
        "model": (data.get("model") or "").strip(),
        "year": (data.get("year") or "").strip(),
        "km": km,
        "colour": (data.get("colour") or "").strip(),
        "vehicle_type": (data.get("vehicle_type") or "").strip(),
        "confidence": (data.get("confidence") or "").strip(),
        "notes": (data.get("notes") or "").strip(),
    }


PHOTO_INTAKE_HTML = r"""
<style>
#photoIntakeBtn{
  position:fixed;
  bottom:170px;
  right:90px;
  width:56px;
  height:56px;
  border-radius:50%;
  background:linear-gradient(135deg,#8b5cf6,#6d28d9);
  color:#fff;
  border:2px solid rgba(255,255,255,.15);
  font-size:24px;
  cursor:pointer;
  z-index:9994;
  box-shadow:
    0 8px 24px rgba(139,92,246,.5),
    inset 0 2px 0 rgba(255,255,255,.25);
  display:flex;
  align-items:center;
  justify-content:center;
  transition:transform .15s ease;
}
#photoIntakeBtn:active{transform:scale(.92);}

#piModal{
  display:none;
  position:fixed;
  inset:0;
  background:#0a1018;
  z-index:9999;
  overflow:auto;
  color:#e6edf5;
}
#piModal.open{display:block;animation:piIn .3s ease;}
@keyframes piIn{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
#piInner{
  max-width:680px;
  margin:0 auto;
  padding:16px;
  min-height:100vh;
}
.piHeader{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding-bottom:14px;
  border-bottom:2px solid #1e2938;
  margin-bottom:16px;
}
.piHeader h2{
  font-size:18px;
  font-weight:800;
  color:#8b5cf6;
  margin:0;
}
.piClose{
  background:#1e2938;
  color:#fff;
  border:none;
  border-radius:8px;
  padding:8px 14px;
  font-size:14px;
  cursor:pointer;
}
.piCard{
  background:#0f1520;
  border:1px solid #1e2938;
  border-radius:12px;
  padding:16px;
  margin-bottom:14px;
}
.piLabel{
  font-size:11px;
  color:#7b8da3;
  letter-spacing:.08em;
  text-transform:uppercase;
  margin-bottom:8px;
  font-weight:700;
}
.piInput{
  width:100%;
  padding:14px;
  background:#0a1018;
  border:1px solid #1e2938;
  border-radius:10px;
  color:#e6edf5;
  font-size:15px;
  box-sizing:border-box;
  font-family:inherit;
  margin-bottom:10px;
}
.piInput:focus{
  outline:none;
  border-color:#8b5cf6;
  box-shadow:0 0 0 2px rgba(139,92,246,.25);
}
.piBtn{
  width:100%;
  padding:16px;
  background:linear-gradient(180deg,#8b5cf6 0%,#6d28d9 100%);
  color:#fff;
  border:none;
  border-radius:10px;
  font-size:15px;
  font-weight:800;
  cursor:pointer;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.2),
    0 6px 16px rgba(139,92,246,.4);
  margin-bottom:8px;
}
.piBtn:active{transform:translateY(2px);}
.piBtn.dark{background:#1e2938;box-shadow:none;}
.piBtn.green{background:linear-gradient(180deg,#10b981,#059669);box-shadow:0 6px 16px rgba(16,185,129,.4);}

.piPhotoPick{
  width:100%;
  padding:24px;
  background:#0a1018;
  border:2px dashed #8b5cf6;
  border-radius:12px;
  text-align:center;
  cursor:pointer;
  color:#8b5cf6;
  font-weight:700;
  margin-bottom:12px;
}
.piPhotoPick:active{background:rgba(139,92,246,.1);}
.piPhotoPick input{display:none;}

.piPreview{
  width:100%;
  border-radius:12px;
  margin-bottom:12px;
  border:1px solid #1e2938;
}

.piResult{display:none;margin-top:14px;}
.piResultRow{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:10px 0;
  border-bottom:1px solid #1e2938;
  font-size:14px;
}
.piResultRow:last-child{border-bottom:none;}
.piResultRow .k{color:#7b8da3;font-size:12px;text-transform:uppercase;letter-spacing:.05em;}
.piResultRow .v{color:#e6edf5;font-weight:700;font-family:'JetBrains Mono','Consolas',monospace;}
.piResultRow .v.empty{color:#4a5568;font-weight:400;}

.piConfidence{
  display:inline-block;
  padding:3px 10px;
  border-radius:10px;
  font-size:10px;
  font-weight:800;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.piConfidence.high{background:#10b981;color:#001a10;}
.piConfidence.medium{background:#f59e0b;color:#1a0d00;}
.piConfidence.low{background:#ef4444;color:#fff;}

.piSpinner{
  text-align:center;
  padding:30px 20px;
  color:#8b5cf6;
  font-size:14px;
  font-weight:600;
}
.piSpinner::before{
  content:'';
  display:block;
  width:32px;
  height:32px;
  margin:0 auto 14px;
  border:3px solid #1e2938;
  border-top-color:#8b5cf6;
  border-radius:50%;
  animation:piSpin .8s linear infinite;
}
@keyframes piSpin{to{transform:rotate(360deg);}}
</style>

<button id="photoIntakeBtn" onclick="piOpen()" title="New Job from Photo">📸</button>

<div id="piModal">
  <div id="piInner">
    <div class="piHeader">
      <h2>📸 New Job from Photo</h2>
      <button class="piClose" onclick="piClose()">✕</button>
    </div>

    <div class="piCard">
      <div class="piLabel">1. Take a photo</div>
      <div style="font-size:12px;color:#7b8da3;margin-bottom:12px;line-height:1.5;">
        Point at a VIN sticker, license plate, dashboard, or odometer.
        AI will read the vehicle details automatically.
      </div>
      <label class="piPhotoPick">
        📷 Tap to take or choose photo
        <input type="file" id="piPhotoInput" accept="image/*" capture="environment" onchange="piPhotoChosen(event)">
      </label>
      <img id="piPreview" class="piPreview" style="display:none;">
    </div>

    <div id="piLoading" class="piCard" style="display:none;">
      <div class="piSpinner">Reading vehicle details…</div>
    </div>

    <div id="piResultCard" class="piCard piResult">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <div class="piLabel" style="margin:0;">2. Confirm details</div>
        <span id="piConfidence" class="piConfidence"></span>
      </div>
      <div id="piResultRows"></div>
      <div style="font-size:11px;color:#7b8da3;margin-top:12px;line-height:1.5;">
        Edit anything before creating the job.
      </div>
    </div>

    <button id="piSubmitBtn" class="piBtn green" style="display:none;" onclick="piCreateJob()">
      ✅ Create Job Card
    </button>
    <button class="piBtn dark" onclick="piReset()">🔄 Try Another Photo</button>
    <div id="piError" style="color:#ef4444;font-size:13px;text-align:center;margin-top:10px;display:none;"></div>
  </div>
</div>

<script>
var _piData = null;

function piOpen(){
  document.getElementById('piModal').classList.add('open');
  piReset();
}
function piClose(){
  document.getElementById('piModal').classList.remove('open');
}
function piReset(){
  _piData = null;
  document.getElementById('piPreview').style.display = 'none';
  document.getElementById('piPreview').src = '';
  document.getElementById('piPhotoInput').value = '';
  document.getElementById('piResultCard').style.display = 'none';
  document.getElementById('piSubmitBtn').style.display = 'none';
  document.getElementById('piLoading').style.display = 'none';
  document.getElementById('piError').style.display = 'none';
  document.getElementById('piError').textContent = '';
}

async function piPhotoChosen(e){
  var file = e.target.files[0];
  if(!file) return;

  // Show preview
  var reader = new FileReader();
  reader.onload = function(ev){
    document.getElementById('piPreview').src = ev.target.result;
    document.getElementById('piPreview').style.display = 'block';
  };
  reader.readAsDataURL(file);

  // Compress + send
  var b64 = await piCompress(file, 1400, 0.8);
  document.getElementById('piLoading').style.display = 'block';
  document.getElementById('piError').style.display = 'none';

  try{
    var resp = await fetch('/api/photo/intake', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ image_base64: b64 })
    });
    var d = await resp.json();

    document.getElementById('piLoading').style.display = 'none';

    if(!d.success){
      document.getElementById('piError').textContent = d.error || 'Failed to read photo';
      document.getElementById('piError').style.display = 'block';
      return;
    }

    _piData = d;
    piRenderResult(d);
  } catch(err){
    document.getElementById('piLoading').style.display = 'none';
    document.getElementById('piError').textContent = 'Network error: ' + err.message;
    document.getElementById('piError').style.display = 'block';
  }
}

function piCompress(file, maxWidth, quality){
  return new Promise(function(resolve){
    var reader = new FileReader();
    reader.onload = function(e){
      var img = new Image();
      img.onload = function(){
        var canvas = document.createElement('canvas');
        var w = img.width, h = img.height;
        if(w > maxWidth){ h = (h * maxWidth) / w; w = maxWidth; }
        canvas.width = w;
        canvas.height = h;
        canvas.getContext('2d').drawImage(img, 0, 0, w, h);
        var dataUrl = canvas.toDataURL('image/jpeg', quality);
        resolve(dataUrl.split(',')[1]);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

function piRenderResult(d){
  var rows = [
    ['VIN', d.vin],
    ['Registration', d.registration],
    ['Make', d.make],
    ['Model', d.model],
    ['Year', d.year],
    ['Odometer', d.km ? d.km + ' km' : ''],
    ['Colour', d.colour],
    ['Vehicle type', d.vehicle_type]
  ];
  var h = '';
  rows.forEach(function(r, i){
    var val = (r[1] || '').toString().trim();
    var display = val || '— not visible —';
    var cls = val ? 'v' : 'v empty';
    h += '<div class="piResultRow">';
    h += '<span class="k">' + r[0] + '</span>';
    h += '<span class="' + cls + '" contenteditable="true" data-field="' + r[0].toLowerCase() + '">' + display + '</span>';
    h += '</div>';
  });

  if(d.notes){
    h += '<div style="margin-top:12px;padding:10px;background:#0a1018;border-radius:8px;font-size:12px;color:#94a3b8;line-height:1.5;">';
    h += '<strong style="color:#f59e0b;">AI notes:</strong> ' + d.notes;
    h += '</div>';
  }

  document.getElementById('piResultRows').innerHTML = h;
  document.getElementById('piResultCard').style.display = 'block';
  document.getElementById('piSubmitBtn').style.display = 'block';

  var conf = (d.confidence || '').toLowerCase();
  var badge = document.getElementById('piConfidence');
  badge.textContent = conf ? conf + ' confidence' : '';
  badge.className = 'piConfidence ' + (conf || 'medium');
}

async function piCreateJob(){
  if(!_piData) return;

  // Read edited values
  var edited = {};
  document.querySelectorAll('#piResultRows [contenteditable]').forEach(function(el){
    var field = el.getAttribute('data-field');
    var val = el.textContent.trim();
    if(val === '— not visible —') val = '';
    edited[field] = val;
  });

  // Prepare the job payload
  var reg = (edited.registration || '').toUpperCase();
  var make = edited.make || '';
  var model = edited.model || '';
  var year = edited.year || '';
  var vehicle = (year ? year + ' ' : '') + (make ? make + ' ' : '') + (model || '');

  var km = parseInt((edited.odometer || '').replace(/\D/g, '')) || 0;

  var payload = {
    customer: '',
    phone: '',
    vehicle: vehicle.trim(),
    registration: reg,
    km: km,
    complaint: 'Vehicle check-in via photo',
    assigned_to: '',
    photos: [_piData.image_base64 || ''],
    signature: '',
    warranty_months: 6
  };

  try{
    var resp = await fetch('/api/jobs', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    var d = await resp.json();

    if(d.success){
      if(window.dpToast) dpToast('Job created: ' + d.job.id, 'success');
      piClose();

      // Jump to jobs tab and reload
      if(typeof showTab === 'function'){
        var navs = document.querySelectorAll('.bnav-item');
        if(navs[3]) navs[3].click();
      }
      setTimeout(function(){
        if(typeof loadJobs === 'function') loadJobs();
      }, 400);
    } else {
      document.getElementById('piError').textContent = 'Failed to create job';
      document.getElementById('piError').style.display = 'block';
    }
  } catch(err){
    document.getElementById('piError').textContent = 'Network error: ' + err.message;
    document.getElementById('piError').style.display = 'block';
  }
}

function piInject(){
  var jobsTab = document.getElementById('jobs');
  if(!jobsTab || document.getElementById('piInlineBtn')) return;
  var title = jobsTab.querySelector('.panel-title');
  if(!title) return;
  var btn = document.createElement('button');
  btn.id = 'piInlineBtn';
  btn.className = 'btn';
  btn.style.cssText = 'background:linear-gradient(135deg,#8b5cf6,#6d28d9);margin-bottom:10px;';
  btn.textContent = '📸 New Job from Photo';
  btn.onclick = piOpen;
  title.parentNode.insertBefore(btn, title.nextSibling);
}

setInterval(function(){ piInject(); }, 900);
setTimeout(function(){ piInject(); }, 600);
</script>
"""
