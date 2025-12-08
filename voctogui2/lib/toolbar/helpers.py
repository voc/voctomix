#!/usr/bin/env python3
import os

def mark_label(btn):
    label = btn.get_label()
    label = label.replace('▶ ','').replace(' ◀','')
    label = "▶ " + label + " ◀"
    btn.set_label(label)

def unmark_label(btn):
    label = btn.get_label()
    label = label.replace('▶ ','').replace(' ◀','')
    btn.set_label(label)

def top_dir_path():
    return os.path.dirname(os.path.abspath(__file__ + '/../..'))


def icon_path():
    return os.path.join(top_dir_path(), 'ui')
