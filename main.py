import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("korea_insects.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            korean_name TEXT NOT NULL,
            habitat TEXT,
            breeding_season TEXT,
            ecology TEXT
        )
    """)
    conn.commit()
    conn.close()


class InsectApp:

    def __init__(self, root):
        self.root = root
        self.root.title("한국 곤충 생태 백과")
        self.root.geometry("650x600")

        # 메인 프레임 설정
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 입력 필드 정의
        labels = [
            ("학명:", "sci_name"),
            ("이름(국명):", "kor_name"),
            ("서식지:", "habitat"),
            ("번식 시기:", "breeding"),
        ]

        self.inputs = {}

        # General Entry Fields
        for i, (label_text, key) in enumerate(labels):
            lbl = tk.Label(main_frame, text=label_text, anchor="e")
            lbl.grid(row=i, column=0, padx=5, pady=5, sticky="e")

            entry = tk.Entry(main_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.inputs[key] = entry

        # Text Field (생태 특징)
        lbl_eco = tk.Label(main_frame, text="생태 특징:", anchor="e")
        lbl_eco.grid(row=4, column=0, padx=5, pady=5, sticky="ne")

        txt_eco = tk.Text(main_frame, width=40, height=4)
        txt_eco.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.inputs["ecology"] = txt_eco

        # 버튼 프레임
        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)

        tk.Button(
            btn_frame, text="정보 등록", width=12, command=self.add_insect
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="이름 검색", width=12, command=self.search_insect
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="전체 목록", width=12, command=self.load_all
        ).pack(side=tk.LEFT, padx=5)

        # 데이터 목록 (Treeview)
        tree_frame = tk.Frame(main_frame)
        tree_frame.grid(
            row=6, column=0, columnspan=2, sticky="nsew", pady=10
        )

        main_frame.grid_rowconfigure(6, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("학명", "이름", "서식지", "번식기", "생태"),
            show="headings",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("학명", text="학명")
        self.tree.heading("이름", text="이름")
        self.tree.heading("서식지", text="서식지")
        self.tree.heading("번식기", text="번식 시기")
        self.tree.heading("생태", text="생태 특징")

        self.tree.column("학명", width=120)
        self.tree.column("이름", width=100)
        self.tree.column("서식지", width=100)
        self.tree.column("번식기", width=90)
        self.tree.column("생태", width=180)

        self.tree.pack(fill=tk.BOTH, expand=True)

        init_db()
        self.load_all()

    def add_insect(self):
        sci_name = self.inputs["sci_name"].get().strip()
        kor_name = self.inputs["kor_name"].get().strip()
        habitat = self.inputs["habitat"].get().strip()
        breeding = self.inputs["breeding"].get().strip()
        ecology = self.inputs["ecology"].get("1.0", tk.END).strip()

        if not sci_name or not kor_name:
            messagebox.showwarning(
                "입력 오류", "학명과 이름은 필수 입력 항목입니다."
            )
            return

        conn = sqlite3.connect("korea_insects.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO insects (scientific_name, korean_name, habitat, breeding_season, ecology)
            VALUES (?, ?, ?, ?, ?)
        """,
            (sci_name, kor_name, habitat, breeding, ecology),
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("성공", "곤충 정보가 등록되었습니다.")
        self.clear_entries()
        self.load_all()

    def search_insect(self):
        target_name = self.inputs["kor_name"].get().strip()
        if not target_name:
            messagebox.showwarning(
                "검색 오류", "검색할 곤충 이름을 입력해주세요."
            )
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect("korea_insects.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT scientific_name, korean_name, habitat, breeding_season, ecology FROM insects WHERE korean_name LIKE ?",
            (f"%{target_name}%",),
        )
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def load_all(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect("korea_insects.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT scientific_name, korean_name, habitat, breeding_season, ecology FROM insects"
        )
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def clear_entries(self):
        for key, widget in self.inputs.items():
            if key == "ecology":
                widget.delete("1.0", tk.END)
            else:
                widget.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = InsectApp(root)
    root.mainloop()
