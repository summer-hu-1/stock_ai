#!/usr/bin/env python3

with open('app.py', 'r') as f:
    lines = f.readlines()

# 找到所有需要调整的块
# 从 "st.set_page_config" 开始到文件结束
# 这些代码应该在顶层（0缩进）

output_lines = []
in_main_section = False

for i, line in enumerate(lines):
    # 找到st.set_page_config作为主逻辑的起点
    if 'st.set_page_config' in line and 'AI看盘助手' in line:
        in_main_section = True

    if in_main_section:
        # 移除前导空格（如果有）
        stripped = line.lstrip()
        leading_spaces = len(line) - len(stripped)

        # 如果行是非空行且有缩进
        if stripped and leading_spaces > 0:
            # 保持4空格的相对缩进结构，但减少到最小
            # 假设原始代码使用的是4空格缩进
            new_leading = leading_spaces
            # 但不能比上一个非空行的缩进更深太多
            output_lines.append(stripped)
        else:
            output_lines.append(line)
    else:
        output_lines.append(line)

# 直接写入
with open('app.py', 'w') as f:
    f.writelines(output_lines)

print("Fixed indentation")
