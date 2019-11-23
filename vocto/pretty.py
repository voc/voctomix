# for parsing configuration items
import re

def pretty(pipe):
    result = ""
    for line in pipe.splitlines():
        line = line.strip()
        r = re.match(r'^(!\s.*)$', line)
        if r:
            result += "    " + r.group(1)
        else:
            r = re.match(r'^([\w\-_]*\s*\=\s*.*)$', line)
            if r:
                result += "        " + r.group(1)
            else:
                r = re.match(r'^(\))$', line)
                if r:
                    result += r.group(1)
                else:
                    r = re.match(r'^bin.\($', line)
                    if r:
                        result += line
                    else:
                        result += "    " + line
        result += "\n"
    return result
