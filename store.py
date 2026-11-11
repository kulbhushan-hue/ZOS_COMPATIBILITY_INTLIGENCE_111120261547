"""Durable SQLite snapshot storage for scraped vendor assertions and source evidence."""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable

DEFAULT_DB = Path(__file__).resolve().parent / 'state' / 'compatibility.sqlite3'

@contextmanager
def connect(path: str | Path = DEFAULT_DB):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(str(path),timeout=15)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA busy_timeout=15000')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL, captured_at TEXT NOT NULL,
      row_count INTEGER NOT NULL, stats_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS observations (
      snapshot_id INTEGER NOT NULL, row_key TEXT NOT NULL, vendor TEXT NOT NULL,
      product TEXT NOT NULL, vrm TEXT NOT NULL, zos_version TEXT NOT NULL,
      status TEXT NOT NULL, ptfs_json TEXT NOT NULL, links_json TEXT NOT NULL,
      ptf_links_present INTEGER NOT NULL DEFAULT 0,
      source_url TEXT NOT NULL, evidence_status TEXT NOT NULL, display_name TEXT NOT NULL,
      PRIMARY KEY(snapshot_id,row_key), FOREIGN KEY(snapshot_id) REFERENCES snapshots(id));
    CREATE TABLE IF NOT EXISTS changes (
      snapshot_id INTEGER NOT NULL, row_key TEXT NOT NULL, change_type TEXT NOT NULL,
      before_json TEXT, after_json TEXT, FOREIGN KEY(snapshot_id) REFERENCES snapshots(id));
    CREATE TABLE IF NOT EXISTS jobs (
      id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT, executed_at TEXT, result TEXT,
      message TEXT, records INTEGER DEFAULT 0);
    CREATE INDEX IF NOT EXISTS idx_obs_match ON observations (vendor, product, vrm, zos_version);
    ''')
    # Existing Cloud deployments may already have the older observations schema.
    cols={row['name'] for row in con.execute('PRAGMA table_info(observations)')}
    if 'ptf_links_present' not in cols:
        con.execute('ALTER TABLE observations ADD COLUMN ptf_links_present INTEGER NOT NULL DEFAULT 0')
        # Reconstruct the link flag from persisted evidence rather than dropping old snapshots.
        for old in con.execute('SELECT rowid,links_json FROM observations').fetchall():
            try:
                links=json.loads(old['links_json'])
                present=any('PTF' in str(x.get('type','')).upper() for x in links)
                con.execute('UPDATE observations SET ptf_links_present=? WHERE rowid=?',(int(present),old['rowid']))
            except (ValueError, TypeError):
                continue
    try:
        with con:
            yield con
    finally:
        con.close()

def key(r):
    return '|'.join(str(r.get(k,'')).strip().casefold() for k in ('vendor','product','vrm','zos_version'))

def compact(r):
    result={k:r.get(k) for k in ('status','ptfs','links','evidence_status','source_url')}
    result['ptf_links_present']=bool(r.get('ptf_links_present')) or any('PTF' in str(x.get('type','')).upper() for x in r.get('links',[]))
    return result

def save(records: list[dict], stats: dict, path=DEFAULT_DB):
    if not records:raise ValueError('Empty crawler results cannot be published')
    vendor=records[0]['vendor']
    if any(r['vendor']!=vendor for r in records):raise ValueError('One vendor per snapshot')
    with connect(path) as conn:
        prev=conn.execute('SELECT id FROM snapshots WHERE vendor=? ORDER BY id DESC LIMIT 1',(vendor,)).fetchone()
        old={}
        if prev:
            for row in conn.execute('SELECT * FROM observations WHERE snapshot_id=?',(prev['id'],)):
                old[row['row_key']]={'status':row['status'],'ptfs':json.loads(row['ptfs_json']),'links':json.loads(row['links_json']),'evidence_status':row['evidence_status'],'source_url':row['source_url'],'ptf_links_present':bool(row['ptf_links_present'])}
        now=datetime.now(timezone.utc).isoformat()
        cur=conn.execute('INSERT INTO snapshots(vendor,captured_at,row_count,stats_json) VALUES(?,?,?,?)',(vendor,now,len(records),json.dumps(stats)))
        snapshot=cur.lastrowid
        new={}
        for r in records:
            k=key(r);c=compact(r);new[k]=c
            conn.execute('''INSERT INTO observations (snapshot_id,row_key,vendor,product,vrm,zos_version,status,ptfs_json,links_json,ptf_links_present,source_url,evidence_status,display_name) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(snapshot,k,r['vendor'],r['product'],r['vrm'],r['zos_version'],r['status'],json.dumps(r.get('ptfs',[])),json.dumps(r.get('links',[])),int(c['ptf_links_present']),r['source_url'],r['evidence_status'],r.get('display_name','')))
            if prev and (k not in old or old[k]!=c):
                conn.execute('INSERT INTO changes VALUES(?,?,?,?,?)',(snapshot,k,'Added' if k not in old else 'Updated',json.dumps(old.get(k)),json.dumps(c)))
        if prev:
            for k,v in old.items():
                if k not in new:conn.execute('INSERT INTO changes VALUES(?,?,?,?,?)',(snapshot,k,'Missing from new source',json.dumps(v),None))
        conn.execute('INSERT INTO jobs(vendor,executed_at,result,message,records) VALUES(?,?,?,?,?)',(vendor,now,'Success','Published validated snapshot',len(records)))
        return snapshot

def record_error(vendor: str, error: str,path=DEFAULT_DB):
    with connect(path) as conn:
        conn.execute('INSERT INTO jobs(vendor,executed_at,result,message,records) VALUES(?,?,?,?,?)',(vendor,datetime.now(timezone.utc).isoformat(),'Failed',str(error)[:800],0))

def latest(vendor='Broadcom',path=DEFAULT_DB):
    with connect(path) as c:
        info=c.execute('SELECT * FROM snapshots WHERE vendor=? ORDER BY id DESC LIMIT 1',(vendor,)).fetchone()
        if not info:return [],None
        records=[]
        for row in c.execute('SELECT * FROM observations WHERE snapshot_id=? ORDER BY product,vrm,zos_version',(info['id'],)):
            r=dict(row);r['ptfs']=json.loads(r.pop('ptfs_json'));r['links']=json.loads(r.pop('links_json'));r['ptf_links_present']=bool(r.get('ptf_links_present')) or any('PTF' in str(x.get('type','')).upper() for x in r['links']);records.append(r)
        return records,dict(info)

def changes(vendor='Broadcom',limit=200,path=DEFAULT_DB):
    with connect(path) as c:
        return [dict(x) for x in c.execute('''SELECT ch.*,s.captured_at FROM changes ch JOIN snapshots s ON s.id=ch.snapshot_id WHERE s.vendor=? ORDER BY ch.snapshot_id DESC LIMIT ?''',(vendor,limit))]

def jobs(limit=30,path=DEFAULT_DB):
    with connect(path) as c:
        return [dict(x) for x in c.execute('SELECT * FROM jobs ORDER BY id DESC LIMIT ?',(limit,))]

def save_vendor_audits(rows: list[dict],path=DEFAULT_DB):
    """Save accessible / blocked source outcomes independently of compatibility assertions."""
    with connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS vendor_audits
            (id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL, source_url TEXT,
             checked_at TEXT NOT NULL, state TEXT NOT NULL, origin TEXT,
             matched_products INTEGER DEFAULT 0, ptf_mentions INTEGER DEFAULT 0,
             note TEXT, matches_json TEXT, assertions_json TEXT)''')
        cols={r['name'] for r in conn.execute('PRAGMA table_info(vendor_audits)')}
        if 'assertions_json' not in cols:conn.execute('ALTER TABLE vendor_audits ADD COLUMN assertions_json TEXT')
        for r in rows:
            conn.execute('''INSERT INTO vendor_audits
              (vendor,source_url,checked_at,state,origin,matched_products,ptf_mentions,note,matches_json,assertions_json)
              VALUES(?,?,?,?,?,?,?,?,?,?)''',
              (r['vendor'],r.get('url',''),r['checked_at'],r['state'],r.get('origin',''),
               r.get('matched_products',0),r.get('ptf_mentions',0),r.get('note',''),json.dumps(r.get('matches',[])),json.dumps(r.get('assertions',[]))))
        return len(rows)


def vendor_audits(path=DEFAULT_DB,limit=1000):
    with connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS vendor_audits
            (id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT NOT NULL, source_url TEXT,
             checked_at TEXT NOT NULL, state TEXT NOT NULL, origin TEXT,
             matched_products INTEGER DEFAULT 0, ptf_mentions INTEGER DEFAULT 0,
             note TEXT, matches_json TEXT, assertions_json TEXT)''')
        cols={r['name'] for r in conn.execute('PRAGMA table_info(vendor_audits)')}
        if 'assertions_json' not in cols:conn.execute('ALTER TABLE vendor_audits ADD COLUMN assertions_json TEXT')
        return [dict(x) for x in conn.execute('SELECT * FROM vendor_audits ORDER BY id DESC LIMIT ?',(limit,))]
