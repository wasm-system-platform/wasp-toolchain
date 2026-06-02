#!/usr/bin/env python3
import os
import sys

os.execvp("llvm-ranlib", ["llvm-ranlib", *sys.argv[1:]])