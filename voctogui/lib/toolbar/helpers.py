#!/usr/bin/env python3

def mark_label(btn):
    label = btn.get_label()
    label = label.replace('▶ ','').replace(' ◀','')
    label = "▶ " + label + " ◀"
    btn.set_label(label)

def unmark_label(btn):
    label = btn.get_label()
    label = label.replace('▶ ','').replace(' ◀','')
    btn.set_label(label)
