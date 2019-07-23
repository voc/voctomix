def quote(str):
    ''' encode spaces and comma '''
    return None if not str else str.replace('\\', '\\\\').replace(' ','\\s').replace(',','\\c').replace('\n','\\n')

def dequote(str):
    ''' decode spaces and comma '''
    return None if not str else str.replace('\\n','\n').replace('\\c', ',').replace('\\s', ' ').replace('\\\\', '\\')