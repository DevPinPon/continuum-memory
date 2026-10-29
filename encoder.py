"""Pinned MiniLM, ONNX CPU execution, masked mean pooling and unit vectors."""
from pathlib import Path
import hashlib,json
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
class Encoder:
    def __init__(self,root=None):
        root=Path(root or Path(__file__).parent/'model')
        opt=ort.SessionOptions();opt.intra_op_num_threads=4;opt.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(root/'onnx/model.onnx'),sess_options=opt,providers=['CPUExecutionProvider'])
        self.tokenizer=Tokenizer.from_file(str(root/'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=256);self.tokenizer.enable_padding(pad_id=0,pad_token='[PAD]')
        self.inputs={x.name for x in self.session.get_inputs()}
        self.signature=hashlib.sha256((root/'onnx/model.onnx').read_bytes()+(root/'tokenizer.json').read_bytes()).hexdigest()
    def encode(self,texts,batch=16):
        out=[]
        for start in range(0,len(texts),batch):
            rows=self.tokenizer.encode_batch(texts[start:start+batch]);ids=np.array([x.ids for x in rows],dtype=np.int64);mask=np.array([x.attention_mask for x in rows],dtype=np.int64)
            inputs=dict(input_ids=ids,attention_mask=mask,token_type_ids=np.array([x.type_ids for x in rows],dtype=np.int64))
            hidden=self.session.run(None,{k:v for k,v in inputs.items() if k in self.inputs})[0]
            if hidden.ndim!=3:raise ValueError('expected token embeddings')
            pooled=(hidden*mask[...,None]).sum(1)/np.maximum(mask.sum(1,keepdims=True),1)
            pooled/=np.maximum(np.linalg.norm(pooled,axis=1,keepdims=True),1e-12);out.append(pooled.astype(np.float32))
        return np.concatenate(out) if out else np.empty((0,384),dtype=np.float32)
