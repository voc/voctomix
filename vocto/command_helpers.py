from typing import Optional, overload


@overload
def quote(value: None) -> None: ...
@overload
def quote(value: str) -> str: ...
def quote(value: Optional[str]) -> Optional[str]:
    ''' encode spaces and comma '''
    return None if not value else value.replace('\\', '\\\\').replace(' ','\\s').replace('|','\\v').replace(',','\\c').replace('\n','\\n')

@overload
def dequote(value: None) -> None: ...
@overload
def dequote(value: str) -> str: ...
def dequote(value: Optional[str]) -> Optional[str]:
    ''' decode spaces and comma '''
    return None if not value else value.replace('\\n','\n').replace('\\c', ',').replace('\\v', '|').replace('\\s', ' ').replace('\\\\', '\\')

def str2bool(value: str) -> bool:
    return value.lower() in [ 'true', 'yes', 'visible', 'show', '1' ]
