#!/usr/bin/env python3
import re

with open('app.py', 'r') as f:
    content = f.read()

# 查找问题区域：找到"with tab1:"之后到"with tab3:"之前的内容
# 这里定义了run_morning_analysis函数和其内部的类和方法

# 替换 tab1 块内的缩进问题
# 问题是 def run_morning_analysis(): 后面应该是 8 空格缩进的函数体

# 简单的替换策略：找到所有连续的多余缩进并修复
lines = content.split('\n')
new_lines = []

i = 0
while i < len(lines):
    line = lines[i]

    # 修复 "def run_morning_analysis():" 之后的缩进
    if 'def run_morning_analysis():' in line:
        new_lines.append(line)
        i += 1
        # 修复函数体内的所有代码（直到遇到同级代码）
        while i < len(lines):
            curr = lines[i]
            if curr.strip() == '':
                new_lines.append(curr)
                i += 1
                continue
            # 检查是否到达了同级代码（不是函数体）
            if not curr.startswith('        '):  # 8空格缩进
                break
            new_lines.append(curr)
            i += 1
    else:
        new_lines.append(line)
        i += 1

# 写回
with open('app.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("Done")
