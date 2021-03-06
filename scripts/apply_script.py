import re
import os

def parse_block(block):
    block = re.sub('\#.*\".*?\".*', '', block)
    strings = re.findall('\".*?\"', block)
    block = re.sub('\".*?\"', ' %s ', block)
    block = re.sub('#.*', '\n', block)
    block = re.sub('(\[\[[\w&$]*\]|\^\^[\w&$]*\^|[\>\<\!\=]+|[\{\}\]^])', r' \1 ', block)
    block = block.strip()

    if block:
        block = re.split('\s+', block)

        if strings:
            i = 0

            for ii in range(len(block)):
                if block[ii] == '%s':
                    block[ii] = strings[i]

                    i += 1

        return block
    else:
        return []

def parse_file(path):
    with open(path, encoding='utf-8-sig') as f:
        file = list()
        stack = [file]
        rhs = False
    
        for token in parse_block(f.read()):
            if token == '=' or token == '>' or token == '<' or token == '>=' or token == '<=' or token == '==' or token == '!=':
                rhs = True

                stack[-1][-1] = [stack[-1][-1], token]
                stack.append(stack[-1][-1])
            elif token == '{':
                stack[-1].append(list())

                if rhs:
                    rhs = False
                    
                    stack.append(stack.pop()[-1])
                else:
                    stack.append(stack[-1][-1])
            elif token == '}' or token == ']' or token == '^':
                stack.pop()
            elif '[[' in token or '^^' in token:
                stack[-1].append([token[1:], list()])
                stack.append(stack[-1][-1][1])
            else:
                stack[-1].append(token)

                if rhs:
                    rhs = False

                    stack.pop()

        return file

def parse_file_block(block):
    block = re.sub('\#.*\".*?\".*', '', block)
    strings = re.findall('\".*?\"', block)
    block = re.sub('\".*?\"', ' %s ', block)
    block = re.sub('#.*', '\n', block)
    block = re.sub('(\[\[[\w&$]*\]|\^\^[\w&$]*\^|[\>\<\!\=]+|[\{\}\]^])', r' \1 ', block)
    block = block.strip()
    block = re.split('\s+', block)

    if strings:
        i = 0

        for ii in range(len(block)):
            if block[ii] == '%s':
                block[ii] = strings[i]

                i += 1
                
    file = list()
    stack = [file]
    rhs = False
    
    for token in block:
        if token == '=' or token == '>' or token == '<' or token == '>=' or token == '<=' or token == '==' or token == '!=':
            rhs = True

            stack[-1][-1] = [stack[-1][-1], token]
            stack.append(stack[-1][-1])
        elif token == '{':
            stack[-1].append(list())

            if rhs:
                rhs = False
                
                stack.append(stack.pop()[-1])
            else:
                stack.append(stack[-1][-1])
        elif token == '}' or token == ']' or token == '^':
            stack.pop()
        elif '[[' in token or '^^' in token:
            stack[-1].append([token[1:], list()])
            stack.append(stack[-1][-1][1])
        else:
            stack[-1].append(token)

            if rhs:
                rhs = False

                stack.pop()

    return file

def apply_macro(file, macros, check=[False]):
    out = list()
    
    for f in file:
        if f and type(f) == type(list()):
            if f[0].count('^') == 2:
                check[0] = True
                
                name = f[0][1:-1]

                for foo in [expand_macro(expand_macro(f[1], f'&{name}&', item), f'&{name}.id&', str(index)) for (index, item) in enumerate(macros[name])]:
                    out.extend(foo)

            else:
                out.append(apply_macro(f, macros, check))
        else:
            out.append(f)

    return out

def expand_macro(content, name, item):
    out = list()

    for c in content:
        if type(c) == type(list()):
            out.append(expand_macro(c, name, item))
        else:
            out.append(c.replace(name, item))

    return out
                        
def apply_script(file, scripts, check=[False]):
    out = list()

    for f in file:
        if f[0] in scripts:
            check[0] = True
            
            if f[2] == 'yes':
                out.extend(apply_paras(scripts[f[0]], []))
            elif f[2] == 'no':
                out.append(['NOT', '=', apply_paras(scripts[f[0]], [])])
            else:
                out.extend(apply_paras(scripts[f[0]], f[2]))
        elif type(f[2]) != type(list()) or not f[2] or type(f[2][0]) != type(list()):
            out.append(f)
        else:
            out.append([f[0], f[1], apply_script(f[2], scripts, check)])
            
    return out

def apply_paras(script, paras):
    out = list()

    for section in script:
        if '[' in section[0]:
            for para in paras:
                if section[0][1:-1] == para[0]:
                    out.extend(apply_paras(section[1], paras))

                    break
        else:
            outout = list()
            
            for part in section[:2]:
                if '$' in part:
                    foo = str(part)
                    
                    for para in paras:
                        foo = foo.replace(f'${para[0]}$', para[2])

                    outout.append(foo)
                else:
                    outout.append(part)
                    
            if type(section[2]) != type(list()):
                if '$' in section[2]:
                    foo = str(section[2])
                    
                    for para in paras:
                        foo = foo.replace(f'${para[0]}$', para[2])

                    outout.append(foo)
                else:
                    outout.append(section[2])
            else:
                outout.append(apply_paras(section[2], paras))

            out.append(outout)
                
    return out

def reconstruct(file, t=''):
    txt = ''

    for f in file:
        if f:
            if len(f) == 3 and type(f[0]) != type(list()) and type(f[1]) != type(list()):
                if type(f[2]) == type(list()):
                    tail = ''
                        
                    if f[2]:
                        if type(f[2][0]) != type(list()):
                            tail = ' '.join(f[2])
                        else:
                            tail = '\n%s%s' % (reconstruct(f[2], t + '\t'), t)

                    txt += '%s%s %s { %s}\n' % (t, f[0], f[1], tail)
                else:
                    txt += '%s%s %s %s\n' % (t, f[0], f[1], f[2])
            elif len(f) == 2 and type(f[0]) != type(list()):
                txt += '%s[%s\n%s%s]\n' % (t, f[0], reconstruct(f[1], t + '\t'), t)

    return txt
            
if __name__ == '__main__':
    import glob

    macros = dict()

    game_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\game"

    for path in glob.glob('macro\\*.txt'):
        file = parse_file(path)

        for macro in file:
            macros[macro[0]] = macro[2]

    patterns = []
    for path in glob.glob(game_path + '\\gfx\\coat_of_arms\\patterns\\*.dds'):
        name = os.path.splitext(os.path.basename(path))[0]
        if " " in name:
            continue
        patterns.append(name)
    macros["patterns"] = patterns

    emblems = []
    for path in glob.glob(game_path + '\\gfx\\coat_of_arms\\colored_emblems\\*.dds'):
        name = os.path.splitext(os.path.basename(path))[0]
        if " " in name:
            continue
        emblems.append(name)
    macros["emblems"] = emblems

    paths = []
    for path in glob.glob("templates\\*"):
        paths.append(path)
    files = [parse_file(path) for path in paths]

    check = [True]

    while check[0]:
        check[0] = False

        for i in range(len(files)):
            files[i] = apply_macro(files[i], macros, check)

    check = [True]
            
    for i in range(len(paths)):
        with open(paths[i].replace("templates", "out"), 'w', encoding='utf-8-sig') as f:
            f.write(reconstruct(files[i]))
