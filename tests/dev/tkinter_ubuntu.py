#! python3  # noqa: E265

"""
    To test https://github.com/Guts/DicoGIS/issues/18
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter.scrolledtext import ScrolledText

root = tk.Tk()
frame = tk.LabelFrame(root, text="Polices")
frame.grid()
ft = tkfont.families()
txt = ScrolledText(frame, width=50, height=20)
txt.grid()

txt.insert("1.0", "Polices:\n")
txt.tag_add("tagpolices", "1.0", "insert")

for i, f in enumerate(ft):
    font = tkfont.Font(frame, size=20, family=f)
    tag = f"tag{i}"
    txt.tag_config(tag, font=font)
    txt.insert("end", f, tag, "\n")

root.mainloop()
