import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS flashcard_sets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS flashcards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        set_id INTEGER NOT NULL,
                        word TEXT NOT NULL,
                        definition TEXT NOT NULL,
                        FOREIGN KEY (set_id) REFERENCES flashcard_sets(id))''')
    conn.commit()

def add_set(conn, name):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO flashcard_sets (name) VALUES (?)', (name,))
    conn.commit()
    return cursor.lastrowid

def add_card(conn, set_id, word, definition):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO flashcards (set_id, word, definition) VALUES (?, ?, ?)',
                   (set_id, word, definition))
    conn.commit()
    return cursor.lastrowid

def get_sets(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM flashcard_sets')
    rows = cursor.fetchall()
    return {row[1]: row[0] for row in rows}

def get_cards(conn, set_id):
    cursor = conn.cursor()
    cursor.execute('SELECT word, definition FROM flashcards WHERE set_id = ?', (set_id,))
    return [(row[0], row[1]) for row in cursor.fetchall()]

def delete_set(conn, set_id):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM flashcard_sets WHERE id = ?', (set_id,))
    conn.commit()

class FlashcardApp:
    def __init__(self, root):
        self.conn = sqlite3.connect('flashcards.db')
        create_tables(self.conn)

        self.current_cards = []
        self.card_index = 0

        self.set_name_var = tk.StringVar()
        self.word_var = tk.StringVar()
        self.definition_var = tk.StringVar()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        self.create_set_frame = self.create_set_tab()
        self.select_set_frame = self.select_set_tab()
        self.flashcard_frame = self.learn_mode_tab()

        self.populate_sets_combobox()

    def create_set_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Create Set')

        ttk.Label(frame, text='Set Name:').pack(padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.set_name_var, width=30).pack(padx=5, pady=5)

        ttk.Label(frame, text='Word:').pack(padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.word_var, width=30).pack(padx=5, pady=5)

        ttk.Label(frame, text='Definition:').pack(padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.definition_var, width=30).pack(padx=5, pady=5)

        ttk.Button(frame, text='Add Word', command=self.add_word).pack(padx=5, pady=10)
        ttk.Button(frame, text='Save Set', command=self.create_set).pack(padx=5, pady=10)

        return frame

    def select_set_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Select Set")

        self.sets_combobox = ttk.Combobox(frame, state='readonly')
        self.sets_combobox.pack(padx=5, pady=5)

        ttk.Button(frame, text='Select Set', command=self.select_set).pack(padx=5, pady=5)
        ttk.Button(frame, text='Delete Set', command=self.delete_selected_set).pack(padx=5, pady=5)

        return frame

    def learn_mode_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Learn Mode')

        self.word_label = ttk.Label(frame, text='', font=('TkDefaultFont', 24))
        self.word_label.pack(padx=5, pady=40)

        self.definition_label = ttk.Label(frame, text='')
        self.definition_label.pack(padx=5, pady=5)

        ttk.Button(frame, text='Flip', command=self.flip_card).pack(side='left', padx=5, pady=5)
        ttk.Button(frame, text='Next', command=self.next_card).pack(side='right', padx=5, pady=5)
        ttk.Button(frame, text='Previous', command=self.prev_card).pack(side='left', padx=5, pady=5)

        return frame

    def populate_sets_combobox(self):
        self.sets_combobox['values'] = tuple(get_sets(self.conn).keys())

    def create_set(self):
        set_name = self.set_name_var.get()
        if set_name and set_name not in get_sets(self.conn):
            add_set(self.conn, set_name)
            self.populate_sets_combobox()
            self.clear_input_fields()

    def add_word(self):
        set_name = self.set_name_var.get()
        word = self.word_var.get()
        definition = self.definition_var.get()

        if set_name and word and definition:
            sets = get_sets(self.conn)
            if set_name not in sets:
                set_id = add_set(self.conn, set_name)
            else:
                set_id = sets[set_name]
            add_card(self.conn, set_id, word, definition)
            self.clear_input_fields()
            self.populate_sets_combobox()

    def clear_input_fields(self):
        self.set_name_var.set('')
        self.word_var.set('')
        self.definition_var.set('')

    def delete_selected_set(self):
        set_name = self.sets_combobox.get()
        if set_name:
            result = messagebox.askyesno('Confirmation', f'Are you sure you want to delete the "{set_name}" set?')
            if result:
                set_id = get_sets(self.conn)[set_name]
                delete_set(self.conn, set_id)
                self.populate_sets_combobox()
                self.clear_flashcard_display()

    def select_set(self):
        set_name = self.sets_combobox.get()
        if set_name:
            set_id = get_sets(self.conn)[set_name]
            self.current_cards = get_cards(self.conn, set_id)
            if self.current_cards:
                self.card_index = 0
                self.show_card()
            else:
                self.word_label.config(text="No cards in this set")
                self.definition_label.config(text='')

    def clear_flashcard_display(self):
        self.word_label.config(text='')
        self.definition_label.config(text='')

    def show_card(self):
        if self.current_cards:
            word, _ = self.current_cards[self.card_index]
            self.word_label.config(text=word)
            self.definition_label.config(text='')

    def flip_card(self):
        if self.current_cards:
            _, definition = self.current_cards[self.card_index]
            self.definition_label.config(text=definition)

    def next_card(self):
        if self.current_cards:
            self.card_index = min(self.card_index + 1, len(self.current_cards) - 1)
            self.show_card()

    def prev_card(self):
        if self.current_cards:
            self.card_index = max(self.card_index - 1, 0)
            self.show_card()

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Flashcard App')
    root.geometry('500x400')
    app = FlashcardApp(root)
    root.mainloop()

