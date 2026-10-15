from flask import Flask, request, render_template_string, redirect
import json
import os
from datetime import date

app = Flask(__name__)
DATA_FILE = "leads.json"


def load_leads():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            leads = json.load(file)
            return leads if isinstance(leads, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_leads(leads):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(leads, file, indent=4)


def calculate_score(lead):
    score = 0
    if lead.get("email"):
        score += 25
    if lead.get("company"):
        score += 25
    if lead.get("phone"):
        score += 20
    if lead.get("status") == "Interested":
        score += 30
    return score


def get_priority(score):
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    return "Low"


def prepare_leads(leads):
    for lead in leads:
        lead.setdefault("id", 0)
        lead.setdefault("name", "Unnamed")
        lead.setdefault("company", "")
        lead.setdefault("email", "")
        lead.setdefault("phone", "")
        lead.setdefault("status", "New")
        lead.setdefault("follow_up", "")
        lead["score"] = calculate_score(lead)
        lead["priority"] = get_priority(lead["score"])
    return leads


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Lead Organizer</title>
<style>
* { box-sizing: border-box; }
body { margin:0; font-family:"Segoe UI",Arial,sans-serif; background:#0b1120; color:#e5e7eb; }
.layout { display:flex; min-height:100vh; }
.sidebar { width:235px; background:#101827; border-right:1px solid #253047; padding:28px 18px; flex-shrink:0; }
.brand { color:#60a5fa; font-size:21px; font-weight:750; margin-bottom:38px; }
.nav-item { display:block; color:#cbd5e1; padding:13px; margin-bottom:8px; border-radius:9px; text-decoration:none; background:#1e293b; }
.sidebar-note { color:#94a3b8; font-size:12px; margin-top:35px; line-height:1.7; }
main { flex:1; min-width:0; padding:32px; }
.topbar { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; margin-bottom:28px; }
h1 { margin:0 0 8px; font-size:30px; color:#f8fafc; }
.subtitle { color:#94a3b8; margin:0; }
.status-pill { border:1px solid #166534; color:#86efac; background:#10291f; padding:9px 13px; border-radius:22px; font-size:13px; }
.stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-bottom:26px; }
.card,.panel { background:#141e30; border:1px solid #253047; border-radius:15px; padding:22px; }
.stat-label { color:#94a3b8; font-size:14px; }
.stat-value { font-size:31px; font-weight:750; margin:13px 0 4px; color:#f8fafc; }
.stat-description { font-size:12px; color:#64748b; }
.blue { border-top:3px solid #3b82f6; } .green { border-top:3px solid #22c55e; } .yellow { border-top:3px solid #eab308; } .purple { border-top:3px solid #a78bfa; }
.content-grid { display:grid; grid-template-columns:minmax(270px,.8fr) minmax(0,1.7fr); gap:22px; align-items:start; }
.panel h2 { margin:0 0 8px; font-size:19px; color:#f8fafc; }
.panel-description { color:#94a3b8; font-size:13px; margin:0 0 22px; }
label { display:block; font-size:13px; color:#cbd5e1; margin:15px 0 7px; }
input,select { width:100%; padding:12px; background:#0b1120; border:1px solid #334155; border-radius:8px; color:#f8fafc; outline:none; }
input:focus,select:focus { border-color:#60a5fa; }
button { cursor:pointer; border:0; border-radius:8px; padding:10px 12px; font-weight:650; }
.primary { width:100%; margin-top:20px; color:white; background:#2563eb; }
.primary:hover { background:#1d4ed8; }
.search-form { display:flex; gap:8px; margin:18px 0; } .search-form input { min-width:0; }
.search-button { background:#334155; color:white; }
.reset-link { display:inline-block; margin-top:8px; color:#93c5fd; text-decoration:none; font-size:13px; }
.table-wrap { overflow-x:auto; }
table { width:100%; border-collapse:collapse; white-space:nowrap; }
th { color:#94a3b8; text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:.5px; padding:14px 12px; border-bottom:1px solid #334155; }
td { padding:13px 12px; border-bottom:1px solid #253047; font-size:13px; }
tbody tr:hover { background:#1b2940; }
.lead-name { font-weight:650; color:#f8fafc; } .company { color:#94a3b8; }
.badge { display:inline-block; padding:5px 9px; border-radius:20px; font-size:11px; font-weight:700; }
.High { background:#123c2a; color:#86efac; } .Medium { background:#443515; color:#fde68a; } .Low { background:#451e2a; color:#fda4af; }
.status { color:#bfdbfe; background:#1e3a5f; }
.delete-button { background:#3f1d2b; color:#fda4af; }
.update-button { background:#1d4ed8; color:white; }
.inline-form { display:flex; flex-direction:column; gap:7px; min-width:145px; }
.inline-form select,.inline-form input { padding:8px; font-size:12px; }
.empty { text-align:center; padding:35px; color:#94a3b8; }
.footer { color:#64748b; font-size:12px; margin-top:25px; }
@media (max-width:1100px) { .stats { grid-template-columns:repeat(2,minmax(0,1fr)); } .content-grid { grid-template-columns:1fr; } }
@media (max-width:650px) { .sidebar { display:none; } main { padding:18px; } h1 { font-size:24px; } .stats { gap:10px; } .card { padding:15px; } .stat-value { font-size:25px; } }
</style>
</head>
<body>
<div class="layout">
<aside class="sidebar">
    <div class="brand">✦ Lead Organizer</div>
    <a class="nav-item" href="/">▦ &nbsp; Dashboard</a>
    <a class="nav-item" href="#add-lead">＋ &nbsp; Add New Lead</a>
    <a class="nav-item" href="#lead-table">☷ &nbsp; All Leads</a>
    <div class="sidebar-note">LEAD MANAGEMENT<br>Organize your business leads and track their priorities.<br><br>Version 1.1</div>
</aside>
<main>
    <div class="topbar">
        <div><h1>Dashboard Overview</h1><p class="subtitle">Welcome back! Here's your lead activity.</p></div>
        <div class="status-pill">● System Running</div>
    </div>
    <section class="stats">
        <div class="card blue"><div class="stat-label">Total Leads</div><div class="stat-value">{{ total }}</div><div class="stat-description">All saved leads</div></div>
        <div class="card green"><div class="stat-label">High Priority</div><div class="stat-value">{{ high }}</div><div class="stat-description">Priority score 70+</div></div>
        <div class="card yellow"><div class="stat-label">Interested Leads</div><div class="stat-value">{{ interested }}</div><div class="stat-description">Interested in your offer</div></div>
        <div class="card purple"><div class="stat-label">Converted Leads</div><div class="stat-value">{{ converted }}</div><div class="stat-description">Marked as converted</div></div>
    </section>
    <section class="content-grid">
        <div class="panel" id="add-lead">
            <h2>＋ Add New Lead</h2><p class="panel-description">Enter the details of a new business lead.</p>
            <form method="POST" action="/add">
                <label>Full Name *</label><input name="name" placeholder="e.g. Ali Khan" required>
                <label>Company</label><input name="company" placeholder="Company name">
                <label>Email Address</label><input name="email" type="email" placeholder="name@example.com">
                <label>Phone Number</label><input name="phone" placeholder="Contact number">
                <label>Lead Status</label><select name="status"><option>New</option><option>Contacted</option><option>Interested</option><option>Converted</option></select>
                <label>Follow-up Date (optional)</label><input name="follow_up" type="date" min="{{ today }}">
                <button class="primary" type="submit">+ Add Lead</button>
            </form>
        </div>
        <div class="panel" id="lead-table">
            <h2>Lead Management</h2><p class="panel-description">Search leads, update their status and set follow-up dates.</p>
            <form class="search-form" method="GET" action="/"><input name="q" value="{{ query }}" placeholder="Search name or company..."><button class="search-button" type="submit">Search</button></form>
            <a class="reset-link" href="/">Clear search</a>
            <div class="table-wrap"><table>
            <thead><tr><th>Lead</th><th>Status</th><th>Score</th><th>Priority</th><th>Follow-up</th><th>Update</th><th>Action</th></tr></thead>
            <tbody>
            {% for lead in leads %}
            <tr>
                <td><div class="lead-name">{{ lead.name }}</div><div class="company">{{ lead.company or 'No company' }}</div></td>
                <td><span class="badge status">{{ lead.status }}</span></td>
                <td>{{ lead.score }}/100</td>
                <td><span class="badge {{ lead.priority }}">{{ lead.priority }}</span></td>
                <td>{{ lead.follow_up or 'Not set' }}</td>
                <td>
                    <form class="inline-form" method="POST" action="/update/{{ lead.id }}">
                        <select name="status" aria-label="Lead status">
                            {% for option in statuses %}<option value="{{ option }}" {% if lead.status == option %}selected{% endif %}>{{ option }}</option>{% endfor %}
                        </select>
                        <input type="date" name="follow_up" value="{{ lead.follow_up }}" min="{{ today }}" aria-label="Follow-up date">
                        <button class="update-button" type="submit">Save Update</button>
                    </form>
                </td>
                <td><form method="POST" action="/delete/{{ lead.id }}" onsubmit="return confirm('Delete this lead?');"><button class="delete-button" type="submit">Delete</button></form></td>
            </tr>
            {% else %}
            <tr><td colspan="7" class="empty">No leads found. Add a lead to get started.</td></tr>
            {% endfor %}
            </tbody></table></div>
        </div>
    </section>
    <div class="footer">AI Lead Organizer · Built with Python and Flask · Priority scores are rule-based estimates.</div>
</main>
</div>
</body>
</html>
"""


@app.route("/")
def home():
    all_leads = prepare_leads(load_leads())
    query = request.args.get("q", "").strip().lower()
    filtered = [
        lead for lead in all_leads
        if query in str(lead.get("name", "")).lower()
        or query in str(lead.get("company", "")).lower()
    ]
    return render_template_string(
        HTML,
        leads=filtered,
        query=query,
        total=len(all_leads),
        high=sum(1 for lead in all_leads if lead["priority"] == "High"),
        interested=sum(1 for lead in all_leads if lead["status"] == "Interested"),
        converted=sum(1 for lead in all_leads if lead["status"] == "Converted"),
        statuses=["New", "Contacted", "Interested", "Converted"],
        today=date.today().isoformat()
    )


@app.route("/add", methods=["POST"])
def add_lead():
    leads = prepare_leads(load_leads())
    name = request.form.get("name", "").strip()
    if not name:
        return redirect("/")
    status = request.form.get("status", "New")
    if status not in ["New", "Contacted", "Interested", "Converted"]:
        status = "New"
    lead = {
        "id": max((int(item.get("id", 0)) for item in leads), default=0) + 1,
        "name": name,
        "company": request.form.get("company", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "status": status,
        "follow_up": request.form.get("follow_up", "").strip()
    }
    lead["score"] = calculate_score(lead)
    lead["priority"] = get_priority(lead["score"])
    leads.append(lead)
    save_leads(leads)
    return redirect("/")


@app.route("/update/<int:lead_id>", methods=["POST"])
def update_lead(lead_id):
    leads = prepare_leads(load_leads())
    allowed_statuses = ["New", "Contacted", "Interested", "Converted"]
    new_status = request.form.get("status", "New")
    if new_status not in allowed_statuses:
        new_status = "New"
    follow_up = request.form.get("follow_up", "").strip()
    for lead in leads:
        if int(lead.get("id", 0)) == lead_id:
            lead["status"] = new_status
            lead["follow_up"] = follow_up
            lead["score"] = calculate_score(lead)
            lead["priority"] = get_priority(lead["score"])
            break
    save_leads(leads)
    return redirect("/")


@app.route("/delete/<int:lead_id>", methods=["POST"])
def delete_lead(lead_id):
    leads = load_leads()
    leads = [lead for lead in leads if int(lead.get("id", 0)) != lead_id]
    save_leads(leads)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
