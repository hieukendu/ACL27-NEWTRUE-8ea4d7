import sys, time; sys.path.insert(0, __file__.rsplit('/',1)[0])
from lm import *
name = sys.argv[1]; bs = int(sys.argv[2])
t=time.time(); tok, model = load(name); print("load", time.time()-t)
ps = [chat(tok, name, None, f"What has Jane Doe {i} done since becoming CEO of Acme Corp?") for i in range(bs*2)]
t=time.time(); out = generate(tok, model, ps, 64, bs); dt=time.time()-t
print(name, "bs", bs, "per-prompt s", dt/len(ps)); print(out[0][:300])
import torch; print("mem GB", torch.mps.driver_allocated_memory()/1e9)
