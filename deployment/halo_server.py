"""Loopback administrative API and CPU embedding worker for cumulative memory."""
import hmac,json,os,sys,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from shared_memory import Memory

ROOT=Path(__file__).resolve().parent

def main():
    os.umask(0o077)
    sys.path.insert(0,str(ROOT.parent/'qwen-context-store-v4'))
    from encoder import Encoder
    auth=ROOT/'private/auth.json'
    if auth.stat().st_mode&0o077:raise RuntimeError('private credentials required')
    token=json.loads(auth.read_text())['token']
    memory=Memory(encoder=Encoder(ROOT.parent/'qwen-context-store-v4/model'))
    def index():
        # Separate encoder instance avoids concurrent tokenizer mutation.
        indexer=Memory(encoder=Encoder(ROOT.parent/'qwen-context-store-v4/model'))
        while True:
            try:n=indexer.index_pending(16)
            except Exception:
                memory.event('index_failure');n=0
            time.sleep(.2 if n else 5)
    threading.Thread(target=index,daemon=True).start()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,data):
            raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def allowed(self):return hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+token)
        def do_GET(self):
            if not self.allowed():return self.reply(401,{'error':'unauthorized'})
            if self.path=='/status':return self.reply(200,memory.status())
            return self.reply(404,{'error':'not found'})
        def do_POST(self):
            if not self.allowed():return self.reply(401,{'error':'unauthorized'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=2*1024*1024:raise ValueError('size')
                body=json.loads(self.rfile.read(size))
                if self.path=='/search':result=memory.search(**body)
                elif self.path=='/publish':result=memory.publish(**body)
                else:return self.reply(404,{'error':'not found'})
                return self.reply(200,result)
            except (ValueError,TypeError,KeyError):return self.reply(400,{'error':'invalid memory request'})
            except Exception:
                memory.event('request_failure');return self.reply(503,{'error':'memory unavailable'})
    # Shared query tokenizer must not be mutated by concurrent HTTP threads.
    from http.server import HTTPServer
    HTTPServer(('127.0.0.1',8748),Handler).serve_forever()

if __name__=='__main__':main()
