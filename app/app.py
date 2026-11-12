#!/usr/bin/env python3
"""AuctionGuard 3 local application. Standard-library HTTP service; pdfplumber optional."""
import csv,io,os,re,json,html,zipfile,pathlib,datetime,threading,webbrowser
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from email.parser import BytesParser
from email.policy import default
from urllib.parse import urlsplit
from auctionguard_engine import screen,TEMPLATE
ROOT=pathlib.Path(__file__).resolve().parent
STATE={'dashboard':None,'stats':None,'warnings':[],'name':''}
H=html.escape
CSS='''<style>:root{color-scheme:dark;--bg:#091321;--panel:#16273c;--line:#334860;--text:#e9f2fb;--muted:#b7c7db;--red:#fb6975;--blue:#69aeff;--green:#56dba0}*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Arial;background:var(--bg);color:var(--text)}header{background:#122035;padding:24px max(20px,calc((100vw - 1480px)/2));border-bottom:1px solid var(--line)}h1{margin:0;font-size:29px}header p{color:var(--muted);margin:6px 0 0}.wrap{max-width:1480px;margin:auto;padding:20px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.bar{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.button,button{font:inherit;background:#2864b0;color:white;padding:12px 19px;border:0;border-radius:9px;cursor:pointer;font-weight:700}.button:hover,button:hover{background:#337cda}.muted{color:var(--muted);font-size:13px;line-height:1.6}.warn{border-left:4px solid #dba551;padding:10px 14px;background:#302a24;border-radius:8px;margin-bottom:10px}.ok{border-left:4px solid var(--green);padding:10px 14px;background:#123a32;border-radius:8px}.flags{display:flex;gap:13px;flex-wrap:wrap;margin-top:10px}.tag{border-radius:7px;padding:7px 10px;background:#1d344c;font-size:13px}.tag.red{color:var(--red)}.tag.blue{color:var(--blue)}.tag.green{color:var(--green)}input[type=file]{display:block;background:#0b1b2d;padding:14px;border:1px dashed #6486ac;border-radius:9px;width:100%;margin:8px 0}iframe{width:100%;height:1020px;border:1px solid #344863;border-radius:12px;background:#0b1221}.links a{color:#8bbdff;margin-right:18px}.hidden{display:none}@media(max-width:750px){.grid{grid-template-columns:1fr}iframe{height:1000px}}</style>'''
PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AuctionGuard 3.0 | Home and Dashboard</title>''' + CSS + '''<header><h1>🛡️ AuctionGuard <span style="color:#69aeff">3.0</span></h1><p>Explainable auction bidding pattern screening · Mac-friendly local research application</p></header><main class="wrap"><div class="panel"><h2>1 · Import and analyse auction data</h2><div class="grid"><div><form id="form"><label><b>Upload auction bids (CSV) and optionally a register (CSV), or text-based Grays PDFs</b><input id="files" name="files" type="file" multiple accept=".csv,.pdf"></label><div class="bar"><button type="submit" id="run">▶ Analyse Data & Show Dashboard</button><button type="button" style="background:#38536e" id="synthetic">Use synthetic demo</button></div></form></div><div><p class="muted"><b>Supported CSV headings:</b> Auction ID, Lot, Pseudonym, Bid Date (DD/MM/YYYY), Bid Time (local as shown), Bid AUD. Optional auction register includes Reported Bids and Source PDF.</p><p class="muted"><b>PDF import:</b> Grays screenshots that contain selectable text; the parser extracts only recognisable rows. Scanned/image PDFs may need OCR outside this tool. Inspect all extracted data before interpreting a flag.</p><div class="flags"><span class="tag red">🔴 Red · Review priority</span><span class="tag blue">🔵 Blue · Contextual indicator</span><span class="tag green">🟢 Green · No configured rule triggered</span></div></div></div><div id="status" class="muted" style="margin-top:16px">Ready. Files are processed locally on this Mac, not uploaded to a remote server.</div></div><div id="results" class="panel hidden"><div class="bar" style="justify-content:space-between"><h2>2 · Interactive results dashboard</h2><div class="links"><a href="/dashboard" target="_blank">Open full-screen ↗</a><a href="/download/bids">Export reviewed bids CSV ↓</a><a href="/download/report">Download HTML dashboard ↓</a></div></div><div id="overview" class="flags"></div><div id="warnings"></div><iframe id="dashboard" title="Interactive auction screening dashboard"></iframe></div><div class="panel muted"><b>Research limitations:</b> Pattern screening is not proof of shill bidding. Pseudonyms do not establish real-world identity. Published Grays PDFs can show incomplete bid histories. Screening colours are not calibrated fraud probabilities. This engine is rule-based, not trained ML or SHAP/LIME.</div></main><script>
const $=s=>document.getElementById(s),status=$('status');
async function run(path,body){$('run').disabled=true;status.textContent='Analysing files locally…';try{const r=await fetch(path,{method:'POST',body});const x=await r.json();if(!r.ok)throw Error(x.error||'Analysis failed');$('results').classList.remove('hidden');$('dashboard').src='/dashboard?t='+Date.now();$('overview').innerHTML=[['Auctions',x.auctions],['Analysed bids',x.records_analysed],['Red',x.red],['Blue',x.blue],['Green',x.green]].map(([k,v])=>`<span class="tag ${k.toLowerCase()}">${k}: <b>${v}</b></span>`).join('');$('warnings').innerHTML=(x.warnings||[]).map(v=>'<p class="warn">'+v.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))+'</p>').join('');status.innerHTML='<span class="ok">Analysis complete. Scroll down to view the dashboard, then select an auction and individual bids.</span>';$('results').scrollIntoView({behavior:'smooth',block:'start'});}catch(e){status.innerHTML='<div class="warn">'+e.message+'</div>'}finally{$('run').disabled=false}}
$('form').onsubmit=e=>{e.preventDefault();const f=$('files').files;if(!f.length){status.textContent='Select PDF/CSV files or use the synthetic demo.';return}let d=new FormData();for(let x of f)d.append('files',x);run('/analyse',d)};
$('synthetic').onclick=()=>run('/synthetic',null);
</script></html>'''

def rows_csv(data):
    text=data.decode('utf-8-sig',errors='replace')
    return list(csv.DictReader(io.StringIO(text)))
def normalise(rows,name):
    out=[];bad=0
    for r in rows:
        normalized={str(k or '').strip():str(v or '').strip() for k,v in r.items()}
        # Support the shipped Grays format and a few obvious column synonyms only
        alias={'Bidder':'Pseudonym','Bidder ID':'Pseudonym','Bid Amount':'Bid AUD','Amount':'Bid AUD','Date':'Bid Date (DD/MM/YYYY)','Time':'Bid Time (local as shown)','Auction':'Auction ID'}
        for a,b in alias.items():
            if b not in normalized and a in normalized:normalized[b]=normalized[a]
        for k in ['Auction ID','Lot','Pseudonym','Bid Date (DD/MM/YYYY)','Bid Time (local as shown)','Bid AUD']:
            if k not in normalized:bad+=1;break
        else:
            normalized.setdefault('Source PDF',name)
            out.append(normalized)
    return out,bad

def extract_pdf(data,name):
    try:import pdfplumber
    except ImportError:raise ValueError('PDF import needs pdfplumber: python3 -m pip install pdfplumber')
    ids=re.findall(r'(?:Lot ID|Lot\s*:)\s*(\d{4})\s*[-–]\s*(\d{7,8})',name,re.I)
    if not ids:ids=re.findall(r'(\d{4})[-–](\d{7,8})',name)
    lot,aid=ids[0] if ids else ('0001',re.search(r'(\d{7,8})',name).group(1) if re.search(r'(\d{7,8})',name) else pathlib.Path(name).stem[:24])
    results=[];rejected=0
    with pdfplumber.open(io.BytesIO(data)) as doc:
      for pn,page in enumerate(doc.pages,1):
        txt=page.extract_text() or ''
        # Grays displayed bidder alias + date/time + price split across lines
        lines=txt.splitlines()
        for i,line in enumerate(lines):
          if not re.search(r'\b\d{2}/\d{2}/\d{4}\b',line):continue
          window=' '.join(lines[max(0,i-1):min(len(lines),i+4)])
          date=re.search(r'\b(\d{2}/\d{2}/\d{4})\b',line)
          price=re.search(r'\$\s*([\d,]+(?:\.\d{1,2})?)',window)
          clock=re.search(r'\b(\d{1,2})[.:](\d{2})[.:](\d{2})\s*(AM|PM)\b',window,re.I)
          if not date or not price or not clock:rejected+=1;continue
          # Date must be on the bidder line; extract alias before the date, excluding adjacent sidebar text
          alias=line.split(date.group(1))[0].strip()
          alias=re.sub(r'^(?:Cars, Bikes & Accessories|Trucks & Trailers|Boats|Wine & More)\s+','',alias,flags=re.I)
          if not (3<=len(alias)<=80):rejected+=1;continue
          try:
            t=datetime.datetime.strptime(f'{clock.group(1)}:{clock.group(2)}:{clock.group(3)} {clock.group(4).upper()}','%I:%M:%S %p').strftime('%H:%M:%S')
            datetime.datetime.strptime(date.group(1),'%d/%m/%Y')
          except ValueError:rejected+=1;continue
          # Must indicate bid qty nearby to reduce contamination from other page text
          if not re.search(r'\bAU\b',window):rejected+=1;continue
          results.append({'Auction ID':aid,'Lot':lot,'Pseudonym':alias,'Bid Date (DD/MM/YYYY)':date.group(1),'Bid Time (local as shown)':t,'Bid AUD':price.group(1).replace(',',''),'Source PDF':name,'Page':pn,'Win Qty':'','Coverage':'PDF-derived; manually verify'})
    unique={}
    for row in results:
        key=tuple(row[k] for k in ['Auction ID','Lot','Pseudonym','Bid Date (DD/MM/YYYY)','Bid Time (local as shown)','Bid AUD'])
        unique[key]=row
    return list(unique.values()),rejected

def analyse(bids,register,warnings,title):
    if not bids:raise ValueError('No valid bid records could be extracted. Verify input CSV headings or PDF bid-history text.')
    for b in bids:b.setdefault('Lot','0001')
    # De-duplicate only exact record identifiers
    unique={}
    for x in bids:
      key=tuple(x.get(k,'') for k in ['Auction ID','Lot','Pseudonym','Bid Date (DD/MM/YYYY)','Bid Time (local as shown)','Bid AUD'])
      unique[key]=x
    if len(unique)<len(bids):warnings.append(f'Removed {len(bids)-len(unique)} exactly duplicated bid rows.')
    bids=list(unique.values())
    auctions,stats=screen(bids,register)
    if stats['unusable_rows']:warnings.append(f"{stats['unusable_rows']} rows had invalid timestamps or amounts and were excluded.")
    if any(a['partial'] for a in auctions):warnings.append('Some auction histories are incomplete or completeness is unknown. Screening evidence applies only to visible rows.')
    dashboard=TEMPLATE.replace('__DATA__',json.dumps({'auctions':auctions,'stats':stats},ensure_ascii=False).replace('</','<\\/')).replace('__RAPID__','60').replace('__REPEAT__','3').replace('__ALTERNATE__','4')
    STATE.update(dashboard=dashboard,stats=stats,warnings=warnings,name=title,auctions=auctions)
    return {**stats,'warnings':warnings}

class Handler(BaseHTTPRequestHandler):
 def respond(self,status,data,kind='text/html; charset=utf-8',download=None):
    if isinstance(data,str):data=data.encode('utf-8')
    self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');
    if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
    self.end_headers();self.wfile.write(data)
 def do_GET(self):
    p=urlsplit(self.path).path
    if p=='/':return self.respond(200,PAGE)
    if p in ['/dashboard','/download/report']:
        if not STATE['dashboard']:return self.respond(404,'Run an analysis first')
        return self.respond(200,STATE['dashboard'],download='AuctionGuard_Investigation.html' if p.endswith('report') else None)
    if p=='/download/bids':
        if not STATE.get('auctions'):return self.respond(404,'Run an analysis first')
        out=io.StringIO();w=csv.writer(out);w.writerow(['Auction ID','Lot','Bid','Pseudonym','Date','Time','Bid AUD','Colour','Triggered rules','Evidence','Source PDF','Page'])
        for a in STATE['auctions']:
            for b in a['rows']:
                w.writerow([a['id'],a['lot'],b['uid'],b['bidder'],b['date'],b['time'],b['amount'],b['level'],'; '.join(q['rule'] for q in b['rules']),'; '.join(q['evidence'] for q in b['rules']),b['source'],b['page']])
        return self.respond(200,out.getvalue(),'text/csv; charset=utf-8','AuctionGuard_Reviewed_Bids.csv')
    self.respond(404,'Not found')
 def do_POST(self):
    p=urlsplit(self.path).path
    try:
      warnings=[]
      if p=='/synthetic':
        sub=ROOT/'sample_data'
        bidfile,regfile=sub/'Synthetic_Demo_Bids.csv',sub/'Synthetic_Demo_Register.csv'
        bids=rows_csv(bidfile.read_bytes());reg=rows_csv(regfile.read_bytes());title='Built-in sample'
        warnings.append('SYNTHETIC dataset: intentionally constructed rule-triggering patterns, not real detected fraud.')
      elif p=='/analyse':
        length=int(self.headers.get('Content-Length','0'))
        if length<=0 or length>70*1024*1024:raise ValueError('Upload must be between 1 byte and 70 MB.')
        blob=self.rfile.read(length)
        msg=BytesParser(policy=default).parsebytes(('Content-Type: '+self.headers.get('Content-Type','')+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+blob)
        files=[(q.get_filename(),q.get_payload(decode=True)) for q in msg.iter_parts() if q.get_filename()]
        if not files:raise ValueError('No files received')
        bids=[];reg=[];title=', '.join(n for n,_ in files)
        for name,data in files:
            if name.lower().endswith('.pdf'):
                found,rejected=extract_pdf(data,name);bids+=found
                warnings.append(f'{name}: {len(found)} PDF-derived bid rows; {rejected} date-containing lines were skipped. Verify aliases, times and prices against the PDF.')
            elif name.lower().endswith('.csv'):
                rows=rows_csv(data)
                if rows and 'Reported Bids' in rows[0] and 'Pseudonym' not in rows[0]:reg+=rows
                else:
                    found,skipped=normalise(rows,name);bids+=found
                    if skipped:warnings.append(f'{name}: {skipped} rows skipped due to missing columns.')
            else: warnings.append(f'{name}: unsupported file type, skipped.')
      else:return self.respond(404,json.dumps({'error':'Invalid route'}),'application/json')
      result=analyse(bids,reg,warnings,title)
      self.respond(200,json.dumps(result),'application/json')
    except Exception as e:self.respond(400,json.dumps({'error':str(e)}),'application/json')
 def log_message(self,*args):pass

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--no-browser',action='store_true');args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    url=f'http://127.0.0.1:{args.port}/'
    print('AuctionGuard running at',url,'\nPress Ctrl+C to stop')
    if not args.no_browser:threading.Timer(.8,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
