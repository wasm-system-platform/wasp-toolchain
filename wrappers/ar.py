#!/usr/bin/env python3
import os
import sys

os.execvp("llvm-ar", ["llvm-ar", *sys.argv[1:]])