import json, hashlib, time, os

AUDIT_LOG = 'runtime/audit/audit_log.json'

def compute_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def sign_entry(event, actor):
    os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
    chain = []
    if os.path.exists(AUDIT_LOG):
        try:
            with open(AUDIT_LOG, 'r') as f: chain = json.load(f)
        except: chain = []
    
    prev_hash = chain[-1]['_hash'] if chain else '0'*64
    entry = {
        'timestamp': time.time(),
        'event': event,
        'actor': actor,
        '_prev_hash': prev_hash
    }
    entry['_hash'] = compute_hash(entry)
    chain.append(entry)
    with open(AUDIT_LOG, 'w') as f: json.dump(chain, f, indent=4)
    return entry

def verify_audit_chain(file_path=None):
    path = file_path or AUDIT_LOG
    if not os.path.exists(path): return {'status': 'missing'}
    try:
        with open(path, 'r') as f: chain = json.load(f)
        for i in range(1, len(chain)):
            if chain[i]['_prev_hash'] != chain[i-1]['_hash']:
                return {'status': 'tampered', 'at_index': i}
        return {'status': 'verified', 'entries': len(chain)}
    except: return {'status': 'corrupted'}

class AuditIntegrity:
    @staticmethod
    def verify(): return verify_audit_chain()