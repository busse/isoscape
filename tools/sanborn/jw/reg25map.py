"""Points between the 1925 half-size scan and the warped frame (the 1952 half-size scan's pixels), by reg25.json."""
import json,numpy as np,cv2,sys
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
R=json.load(open(''+__import__('os').path.join(__import__('os').path.dirname(__file__),'reg25.json')+''))
def T(q): return np.stack([np.ones(len(q)),q[:,0]/1000,q[:,1]/1000,(q[:,0]/1000)**2,q[:,0]*q[:,1]/1e6,(q[:,1]/1000)**2],1)
def h2w(sh,uv):
    r=R[sh]; H=np.array(r['H']); q=cv2.perspectiveTransform(np.asarray(uv,np.float64)[None],H)[0]
    t=T(q); return q+np.stack([t@np.array(r['cu']),t@np.array(r['cv'])],1)
def w2h(sh,uv):
    r=R[sh]; q=np.asarray(uv,float); q0=q.copy()
    for _ in range(3):
        t=T(q0); q0=q-np.stack([t@np.array(r['cu']),t@np.array(r['cv'])],1)
    return cv2.perspectiveTransform(q0[None],np.linalg.inv(np.array(r['H'])))[0]
