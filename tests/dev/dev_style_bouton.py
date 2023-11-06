import tkinter as tk
from tkinter import ttk


def main():
    root = tk.Tk()
    root.title("Style Tkinter pour Ubuntu")

    # Configuration du style
    style = ttk.Style()

    # Configurons un style sympa pour le bouton
    style.configure(
        "TButton",
        foreground="white",
        background="#007BFF",
        padding=10,
        width=20,
        font=("Ubuntu", 12),
    )

    style.map(
        "TButton", background=[("active", "#0056b3")], foreground=[("active", "white")]
    )

    # Configurons un style pour le label
    style.configure(
        "TLabel",
        background="#f5f5f5",
        foreground="#333",
        padding=10,
        font=("Ubuntu", 12),
    )

    # Ajout d'un label et d'un bouton à la fenêtre
    lbl = ttk.Label(root, text="Ceci est un label stylisé")
    lbl.pack(pady=20)

    btn = ttk.Button(root, text="Bouton Stylisé", command=root.quit)
    btn.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()
