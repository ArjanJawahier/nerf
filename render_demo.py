#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os, sys
# os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
os.environ['CUDA_VISIBLE_DEVICES'] = '1'
import tensorflow as tf
tf.compat.v1.enable_eager_execution()

import numpy as np
import imageio
import json
import random
import time
import pprint

import matplotlib.pyplot as plt

import run_nerf

from load_llff import load_llff_data
from load_deepvoxels import load_dv_data
from load_blender import load_blender_data


# In[2]:


basedir = './logs'
# expname = 'fern_example'
expname = 'fern_test'

config = os.path.join(basedir, expname, 'config.txt')
print('Args:')
print(open(config, 'r').read())
parser = run_nerf.config_parser()

# VERY IMPORTANT:
print("Keep in mind the model number of iterations has changed from 200000 to 40000.")
n_iterations = 40000
n_iterations = str(n_iterations).zfill(6)
args = parser.parse_args('--config {} --ft_path {}'.format(config, os.path.join(basedir, expname, f'model_{n_iterations}.npy')))
print('loaded args')

images, poses, bds, render_poses, i_test = load_llff_data(args.datadir, args.factor, 
                                                          recenter=True, bd_factor=.75, 
                                                          spherify=args.spherify)
H, W, focal = poses[0,:3,-1].astype(np.float32)

H = int(H)
W = int(W)
hwf = [H, W, focal]

images = images.astype(np.float32)
poses = poses.astype(np.float32)

if args.no_ndc:
    near = tf.reduce_min(bds) * .9
    far = tf.reduce_max(bds) * 1.
else:
    near = 0.
    far = 1.


# In[3]:


# Create nerf model
_, render_kwargs_test, start, grad_vars, models = run_nerf.create_nerf(args)

bds_dict = {
    'near' : tf.cast(near, tf.float32),
    'far' : tf.cast(far, tf.float32),
}
render_kwargs_test.update(bds_dict)

print('Render kwargs:')
pprint.pprint(render_kwargs_test)


down = 4
render_kwargs_fast = {k : render_kwargs_test[k] for k in render_kwargs_test}
render_kwargs_fast['N_importance'] = 0

c2w = np.eye(4)[:3,:4].astype(np.float32) # identity pose matrix
test = run_nerf.render(H//down, W//down, focal/down, c2w=c2w, **render_kwargs_fast)
img = np.clip(test[0],0,1)
# plt.imshow(img)
# plt.show()


# In[9]:

# down started at 8
down = 1 # trade off resolution+aliasing for render speed to make this video faster
frames = []
for i, c2w in enumerate(render_poses):
    if i%8==0: print(i)
    test = run_nerf.render(H//down, W//down, focal/down, c2w=c2w[:3,:4], **render_kwargs_fast)
    frames.append((255*np.clip(test[0],0,1)).astype(np.uint8))
    
print('done, saving')
f = f'logs/{expname}/video.mp4'
imageio.mimwrite(f, frames, fps=30, quality=8)

from IPython.display import Video
Video(f, height=320)

print("Video has been saved. Good enough for my purposes here.")
print(f"filename: logs/{expname}/video_{n_iterations}.mp4")
# Video has been saved. Good enough for my purposes here.

# # In[4]:


# get_ipython().run_line_magic('matplotlib', 'inline')
# from ipywidgets import interactive, widgets
# import matplotlib.pyplot as plt
# import numpy as np


# def f(x, y, z):
    
#     c2w = tf.convert_to_tensor([
#         [1,0,0,x],
#         [0,1,0,y],
#         [0,0,1,z],
#         [0,0,0,1],
#     ], dtype=tf.float32)
    
#     test = run_nerf.render(H//down, W//down, focal/down, c2w=c2w, **render_kwargs_fast)
#     img = np.clip(test[0],0,1)
    
#     plt.figure(2, figsize=(20,6))
#     plt.imshow(img)
#     plt.show()
    

# sldr = lambda : widgets.FloatSlider(
#     value=0.,
#     min=-1.,
#     max=1.,
#     step=.01,
# )

# names = ['x', 'y', 'z']
    
# interactive_plot = interactive(f, **{n : sldr() for n in names})
# interactive_plot


# In[ ]:




