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


# 앱 클래스 정의
class InsectApp:

    def __init__(self, root):
        self.root = root
        self.root.title("한국 곤충 생태 백과")
        self.root.geometry("600x550")

        # 입력 폼 레이블 및 엔트리
        labels = [
            "학명:",
            "이름(국명):",
            "서식지:",
            "번식 시기:",
            "생태 특징:",
        ]
        self.entries = {}

        for i, text in enumerate(labels):
            lbl = tk.Label(root, text=text)
            lbl.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if text == "생태 특징:":
                entry = tk.Text(root, width=40, height=4)
            else:
                entry = tk.Entry(root, width=40)

            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            self.entries[text] = entry

        # 버튼 영역
        btn_frame = tk.Frame(root)
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

        # 데이터 출력 목록 (Treeview)
        self.tree = ttk.Treeview(
            root,
            columns=("학명", "이름", "서식지", "번식기", "생태"),
            show="headings",
        )
        self.tree.heading("학명", text="학명")
        self.tree.heading("이름", text="이름")
        self.tree.heading("서식지", text="서식지")
        self.tree.heading("번식기", text="번식 시기")
        self.tree.heading("생태", text="생태 특징")

        self.tree.column("학명", width=100)
        self.tree.column("이름", width=80)
        self.tree.column("서식지", width=100)
        self.tree.column("번식기", width=80)
        self.tree.column("생태", width=180)

        self.tree.grid(
            row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew"
        )

        init_db()
        self.load_all()

    def add_insect(self):
        sci_name = self.entries["학명:"].get().strip()
        kor_name = self.entries["이름(국명):"].get().strip()
        habitat = self.entries["서식지:"].get().strip()
        breeding = self.entries["번식 시기:"].get().strip()
        ecology = self.entries["생태 특징:"].get("1.0", tk.END).strip()

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
        target_name = self.entries["이름(국명):"].get().strip()
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
        for key, entry in self.entries.items():
            if key == "생태 특징:":
                entry.delete("1.0", tk.END)
            else:
                entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = InsectApp(root)
    root.mainloop()
