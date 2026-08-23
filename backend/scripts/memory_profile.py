import os
import sys
import psutil

def print_mem(stage):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024
    print(f"[{stage}] Memory Usage: {mem:.2f} MB")

print_mem("Initial")

import torch
print_mem("After import torch")

from sentence_transformers import SentenceTransformer, CrossEncoder
print_mem("After import sentence_transformers")

print("Loading SentenceTransformer...")
# Use eval mode and no_grad
model1 = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
model1.eval()
print_mem("After SentenceTransformer load")

print("Loading CrossEncoder...")
model2 = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
model2.model.eval()
print_mem("After CrossEncoder load")
