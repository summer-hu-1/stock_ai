#!/usr/bin/env python3

with open('app.py', 'r') as f:
    content = f.read()

lines = content.split('\n')

# Find lines 585-651 that need to be re-indented
# They should be at 20 spaces (inside elif) not 16 spaces

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # Lines 585-651 need indent adjustment (inside elif block)
    # We identify them by being after "elif result.get(\"data_collected\"):" (line 585)
    # and before "else:" (line 652)

    if i == 585:  # elif line
        new_lines.append(line)
        i += 1
    elif 586 <= i <= 651:  # content inside elif block
        if line.strip():  # non-empty line
            # Add 4 spaces to existing indentation
            leading_spaces = len(line) - len(line.lstrip())
            new_line = ' ' * (leading_spaces + 4) + line.lstrip()
            new_lines.append(new_line)
        else:
            new_lines.append(line)
        i += 1
    else:
        new_lines.append(line)
        i += 1

with open('app.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("Fixed indentation for elif block content")
