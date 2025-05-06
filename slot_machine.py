import tkinter as tk
from tkinter import messagebox
import random

SYMBOLS = ["🍎", "🍌", "🍒", "⭐", "🍊"]
REWARDS = {
    ("🍎", "🍎", "🍎"): 50,
    ("🍌", "🍌", "🍌"): 30,
    ("🍒", "🍒", "🍒"): 20,
    ("⭐", "⭐", "⭐"): 100,
    ("🍊", "🍊", "🍊"): 40
}

class SlotMachine:
    def __init__(self, root):
        self.root = root
        self.root.title("Jogo do Triguinho")
        self.root.geometry("400x300")
        
        self.points = 100
        
        self.points_label = tk.Label(root, text=f"Pontos: {self.points}", font=("Arial", 14))
        self.points_label.pack(pady=10)
        
        self.reels_frame = tk.Frame(root)
        self.reels_frame.pack(pady=20)
        
        self.reel1 = tk.Label(self.reels_frame, text="🎰", font=("Arial", 30), width=4, relief="sunken")
        self.reel2 = tk.Label(self.reels_frame, text="🎰", font=("Arial", 30), width=4, relief="sunken")
        self.reel3 = tk.Label(self.reels_frame, text="🎰", font=("Arial", 30), width=4, relief="sunken")
        self.reel1.pack(side=tk.LEFT, padx=5)
        self.reel2.pack(side=tk.LEFT, padx=5)
        self.reel3.pack(side=tk.LEFT, padx=5)
        
        self.spin_button = tk.Button(root, text="Girar!", font=("Arial", 12), command=self.spin)
        self.spin_button.pack(pady=20)
        
        self.result_label = tk.Label(root, text="", font=("Arial", 12))
        self.result_label.pack(pady=10)
    
    def spin(self):
        if self.points < 10:
            messagebox.showwarning("Sem pontos", "Você precisa de pelo menos 10 pontos para girar!")
            return
        
        self.points -= 10
        self.points_label.config(text=f"Pontos: {self.points}")
        
        result = [random.choice(SYMBOLS) for _ in range(3)]
        self.reel1.config(text=result[0])
        self.reel2.config(text=result[1])
        self.reel3.config(text=result[2])
        
        combination = tuple(result)
        if combination in REWARDS:
            reward = REWARDS[combination]
            self.points += reward
            self.result_label.config(text=f"Você ganhou {reward} pontos!", fg="green")
        else:
            self.result_label.config(text="Tente novamente!", fg="red")
        
        self.points_label.config(text=f"Pontos: {self.points}")
        
        if self.points <= 0:
            messagebox.showinfo("Fim de jogo", "Seus pontos acabaram! Reinicie o jogo.")
            self.spin_button.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = SlotMachine(root)
    root.mainloop()