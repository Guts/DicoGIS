import tkinter as tk
from tkinter import ttk


def toggle_widgets_state():
    """Active ou désactive les widgets à l'intérieur du LabelFrame selon l'état de la case à cocher."""
    if check_var.get():
        for widget in frame.winfo_children():
            widget.config(state=tk.NORMAL)
    else:
        for widget in frame.winfo_children():
            widget.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    root.title("LabelFrame Activable")

    # Variable pour la case à cocher
    check_var = tk.IntVar()

    # Checkbutton pour activer/désactiver le LabelFrame
    check_btn = tk.Checkbutton(
        root,
        text="Activer le LabelFrame",
        variable=check_var,
        command=toggle_widgets_state,
    )
    check_btn.pack(pady=10)

    # Création du LabelFrame
    frame = ttk.LabelFrame(root, text="Mon LabelFrame")
    frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    # Ajout d'un widget à l'intérieur du LabelFrame
    entry = ttk.Entry(frame)
    entry.pack(pady=20)

    # Initialise l'état des widgets
    toggle_widgets_state()

    root.mainloop()


if __name__ == "__main__":
    main()
