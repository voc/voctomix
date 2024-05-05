def quote(str):
    '''encode spaces and comma'''
    return (
        None
        if not str
        else str.replace('\\', '\\\\')
        .replace(' ', '\\s')
        .replace('|', '\\v')
        .replace(',', '\\c')
        .replace('\n', '\\n')
    )


def dequote(str):
    '''decode spaces and comma'''
    return (
        None
        if not str
        else str.replace('\\n', '\n')
        .replace('\\c', ',')
        .replace('\\v', '|')
        .replace('\\s', ' ')
        .replace('\\\\', '\\')
    )


def str2bool(str):
    return str.lower() in ['true', 'yes', 'visible', 'show', '1']
