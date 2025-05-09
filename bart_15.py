import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk
import tkinter.simpledialog as simpledialog
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse  # Add this import at the top
from collections import Counter
import random
import time
import os
import sys
import pygame
from dotenv import load_dotenv

pygame.mixer.init()

def resource_path(filename):
    """Get absolute path to resource (for PyInstaller .exe compatibility)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.abspath(filename)

def play_pop_sound():
    try:
        pygame.mixer.music.load(resource_path("pop.mp3"))
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

def add_signup_instructions(frame):
    title_font = tkFont.Font(family="Arial", size=18, weight="bold")
    tk.Label(frame, text="Before you begin:", font=title_font, bg='white').pack(pady=(10, 0))
    instructions = (
        "Please ensure you are in a private, quiet place where you will not be interrupted.\n\n"
        "Complete the task leisurely without distractions.\n\n"
        "The highest earner across the experiment will win a prize of 600 EGP!"
    )
    tk.Label(frame, text=instructions, font=("Arial", 14), bg='white', wraplength=700, justify='center').pack(pady=(0, 20))


# === CONFIG ===
load_dotenv()  # Loads .env into environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

PRACTICE_ROUNDS = 5
BASELINE_ROUNDS = 15
PRESSURE_ROUNDS = 15
TIME_PRESSURE_SECONDS = 15
BREAK_SECONDS = 300

BALLOON_MAX_SIZE = 240  
BALLOON_ORIGINAL_SIZE = 52 # Starting Size
BALLOON_GROWTH = 2

random.seed(42)  # Same seed = same random behavior

class BARTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Balloon Analogue Risk Task (BART)")
        # self.root.attributes('-fullscreen', True) Old
        self.root.state('zoomed')  # Fills screen but keeps taskbar
        self.root.focus_force()
        self.canvas = tk.Canvas(root, bg='white')
        self.canvas.pack(fill='both', expand=True)

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
        self.conditions_completed = 0
        self.participant_info = {}
        self.after_id = None

        self.balloon_label = None

        self.balloon = None
        self.balloon_size = BALLOON_ORIGINAL_SIZE
        
        self.max_pumps = 0
        self.pumps = 0
        self.trial_number = 0
        self.running = False
        self.countdown_time = 0
        self.earnings = 0
        self.last_earnings = 0.0
        self.explosion_point = 0
        self.debug_mode_enabled = False
        #self.pending_condition = None
        #self.break_after_id = None

        self.root.bind_all("<Control-Alt-Shift-D>", self.debug_skip_all)


        self.explosion_points = [58, 24, 26, 13, 16, 56, 29, 41, 13, 49, 39, 46, 29, 13, 28]

        #self.root.bind('<m>', lambda e: self.inflate_to_max_size())



        self.setup_intro_screen()
    # def inflate_to_max_size(self):
    #     if not self.running:
    #         return
    #     self.pumps = self.max_pumps
    #     self.balloon_size = BALLOON_MAX_SIZE
    #     self.draw_balloon()
    #     self.balloon_label.config(text="Max Size Reached (Debug)")


    def generate_unique_participant_id(self):
        while True:
            participant_id = str(random.randint(10000000, 99999999))
            try:
                result = self.supabase.table('participants').select('participant_id').eq('participant_id', participant_id).execute()
                if not result.data:
                    return participant_id
            except:
                return participant_id


    def setup_intro_screen(self):
        self.current_page = 0
        self.pages = []

        title_font = tkFont.Font(family="Arial", size=18, weight="bold")

        # === PAGE 1 ===
        page1 = tk.Frame(self.root, bg='white')
        page1.place(relx=0.5, rely=0.5, anchor='center')
        self.pages.append(page1)

        add_signup_instructions(page1)

        tk.Label(page1, text="Age", font=("Arial", 16), bg='white').pack()
        self.age_entry = tk.Entry(page1, font=("Arial", 16), width=30)
        self.age_entry.pack(pady=5)

        tk.Label(page1, text="Major", font=("Arial", 16), bg='white').pack()
        self.major_entry = tk.Entry(page1, font=("Arial", 16), width=30)
        self.major_entry.pack(pady=5)

        tk.Label(page1, text="Standing", font=("Arial", 16), bg='white').pack()
        self.standing_var = tk.StringVar()
        self.standing_dropdown = ttk.Combobox(page1, textvariable=self.standing_var, font=("Arial", 16),
                                            values=["Freshman", "Sophomore", "Junior", "Senior"], state="readonly")
        self.standing_dropdown.pack(pady=5)

        tk.Label(page1, text="Gender", font=("Arial", 16), bg='white').pack()
        self.gender_var = tk.StringVar()
        self.gender_dropdown = ttk.Combobox(page1, textvariable=self.gender_var, font=("Arial", 16),
                                            values=["Male", "Female"], state="readonly")
        self.gender_dropdown.pack(pady=5)

        tk.Button(page1, text="Next", font=("Arial", 16), command=self.next_page).pack(pady=20)

        # === PAGE 2 ===
        page2 = tk.Frame(self.root, bg='white')
        self.pages.append(page2)

        tk.Label(page2, text="Are you Relaxed or Stressed?", font=("Arial", 16), bg='white').pack()
        self.stress_var = tk.StringVar()
        self.stress_dropdown = ttk.Combobox(page2, textvariable=self.stress_var, font=("Arial", 16),
                                            values=["Relaxed", "Stressed"], state="readonly")
        self.stress_dropdown.pack(pady=5)

        tk.Label(page2, text="Sleep Hours", font=("Arial", 16), bg='white').pack()
        self.sleep_entry = tk.Entry(page2, font=("Arial", 16), width=30)
        self.sleep_entry.pack(pady=5)

        caffeine_frame = tk.Frame(page2, bg='white')
        caffeine_frame.pack(pady=5)
        tk.Label(caffeine_frame, text="Caffeine Today?", font=("Arial", 16), bg='white').pack(side='left', padx=5)
        self.caffeine_var = tk.StringVar()
        self.caffeine_dropdown = ttk.Combobox(caffeine_frame, textvariable=self.caffeine_var, font=("Arial", 16),
                                            values=["Yes", "No"], state="readonly", width=5)
        self.caffeine_dropdown.pack(side='left', padx=5)
        self.caffeine_dropdown.bind("<<ComboboxSelected>>", self.show_caffeine_amount)

        self.caffeine_amount_var = tk.StringVar()
        self.caffeine_amount_dropdown = ttk.Combobox(caffeine_frame, textvariable=self.caffeine_amount_var, font=("Arial", 16),
                                                    values=["1 cup", "2 cups", "3 cups", "4 cups", "5 cups", "6+ cups"],
                                                    state="readonly", width=8)

        tk.Button(page2, text="Previous", font=("Arial", 16), command=self.prev_page).pack(side='left', padx=50, pady=20)
        tk.Button(page2, text="Next", font=("Arial", 16), command=self.next_page).pack(side='right', padx=50, pady=20)

        # === PAGE 3 ===
        page3 = tk.Frame(self.root, bg='white')
        self.pages.append(page3)

        tk.Label(page3, text="Have you ever done a task where you repeatedly pumped a balloon to earn money, but it could pop?",
                font=("Arial", 16), bg='white', wraplength=700, justify='center').pack(pady=(10, 0))
        self.bart_familiarity_var = tk.StringVar()
        self.bart_familiarity_dropdown = ttk.Combobox(page3, textvariable=self.bart_familiarity_var, font=("Arial", 16),
                                                    values=["No", "Yes"], state="readonly", width=12)
        self.bart_familiarity_dropdown.pack(pady=5)

        tk.Label(page3, text="Phone or Email (optional for prize):", font=("Arial", 16), bg='white').pack(pady=(20, 0))
        self.contact_entry = tk.Entry(page3, font=("Arial", 16), width=30)
        self.contact_entry.pack(pady=5)

        tk.Button(page3, text="Previous", font=("Arial", 16), command=self.prev_page).pack(side='left', padx=50, pady=20)
        self.start_button = tk.Button(page3, text="Start Task", font=("Arial", 18),
                                    command=self.upload_and_assign_condition, bg='#4CAF50', fg='white')
        self.start_button.pack(side='right', padx=50, pady=20)

        # Start with first page visible
        self.show_page(0)

    def show_page(self, index):
        for i, page in enumerate(self.pages):
            page.place_forget()
        self.pages[index].place(relx=0.5, rely=0.5, anchor='center')
        self.current_page = index

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.show_page(self.current_page + 1)

    def prev_page(self):
        if self.current_page > 0:
            self.show_page(self.current_page - 1)


    def show_caffeine_amount(self, event=None):
        if self.caffeine_var.get() == "Yes":
            self.caffeine_amount_dropdown.pack(side='left', padx=5)
        else:
            self.caffeine_amount_dropdown.pack_forget()
    
    def validate_form(self):
        try:
            age = int(self.age_entry.get())
            if age < 0 or age > 120:
                raise ValueError("Invalid age")

            sleep = float(self.sleep_entry.get())
            if sleep < 0 or sleep > 24:
                raise ValueError("Invalid sleep hours")

            if not all([
                self.major_entry.get().strip(),
                self.standing_var.get(),
                self.gender_var.get(),
                self.stress_var.get(),
                self.caffeine_var.get(),
                self.bart_familiarity_var.get()
            ]):
                raise ValueError("All required fields must be filled")

            if self.caffeine_var.get() == "Yes" and not self.caffeine_amount_var.get():
                raise ValueError("Specify how many cups of caffeine you had")

            if self.bart_familiarity_var.get() == "Yes":
                raise ValueError("Sorry, this study is only for people who have never done a balloon-pumping task before.")

            return True
        except ValueError as e:
            tk.messagebox.showerror("Form Error", str(e))
            return False



    def upload_and_assign_condition(self):
        if not self.validate_form():
            return
        self.participant_id = self.generate_unique_participant_id()

        self.participant_info = {
            "Age": self.age_entry.get(),
            "Major": self.major_entry.get(),
            "Standing": self.standing_var.get(),
            "Gender": self.gender_var.get(),
            "Stress Level": self.stress_var.get(),
            "Sleep Hours": self.sleep_entry.get(),
            "Caffeine Today": self.caffeine_var.get(),
            "Caffeine Amount": self.caffeine_amount_var.get() if self.caffeine_var.get() == "Yes" else "0",
            "participant_id": self.participant_id
        }

        # Get current time
        now = datetime.now(timezone.utc)


        # Get gender of participant
        gender = self.participant_info["Gender"]

        try:
            response = self.supabase.table('participants') \
                .select('participant_id, start_condition, submission_time, completed') \
                .eq('gender', gender) \
                .execute()

            participants = response.data or []

            # Filter based on completed=True OR submitted within last 30 minutes
            valid_participants = [
                p for p in participants
                if p.get("completed") is True
                or isoparse(p["submission_time"]) >= now - timedelta(minutes=30)
            ]

            # Count how many did each condition
            condition_counts = Counter(p.get("start_condition") for p in valid_participants if p.get("start_condition") in ["baseline_first", "pressure_first"])

            baseline_count = condition_counts["baseline_first"]
            pressure_count = condition_counts["pressure_first"]

            # Assign to the lesser group
            if baseline_count <= pressure_count:
                flip = "baseline_first"
            else:
                flip = "pressure_first"

        except Exception as e:
            print(f"Error during gender-balanced assignment: {e}")
            # Default to alternating based on random parity to mitigate consistent bias
            flip = random.choice(["baseline_first", "pressure_first"])

        self.participant_info["StartCondition"] = flip


        try:
            self.supabase.table('participants').insert({
                "participant_id": self.participant_id,
                "age": self.participant_info["Age"],
                "gender": self.participant_info["Gender"],
                "major": self.participant_info["Major"],
                "standing": self.participant_info["Standing"],
                "stress_level": self.participant_info["Stress Level"],
                "sleep_hours": self.participant_info["Sleep Hours"],
                "caffeine_today": self.participant_info["Caffeine Today"],
                "caffeine_amount": self.participant_info["Caffeine Amount"],
                "start_condition": flip,
                "submission_time": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            print(f"Failed to upload participant info: {e}")

        contact = self.contact_entry.get().strip()
        if contact:
            try:
                self.supabase.table('contacts').insert({
                    "participant_id": self.participant_id,
                    "contact_info": contact
                }).execute()
            except Exception as e:
                print(f"Failed to upload contact info: {e}")

        for page in self.pages:
            page.destroy()     
        
        self.root.bind('s', self.skip_practice)

        self.show_instructions("Practice Round Instructions",
            "• Pump the balloon to earn more money — each pump earns $0.05.\n\n"
            "• However, the balloon can burst at any point **without warning**, causing you to lose all earnings for that balloon.\n\n"
            "• You can click 'Collect $$$' at any time to safely collect your current earnings.\n\n"
            "This is a practice round. Press 'S' anytime to skip.\n\n"
            "Click OK to begin."
        )

        
    def show_instructions(self, title, message, next_function=None):
        self.instructions_frame = tk.Frame(self.root, bg='white')
        self.instructions_frame.place(relx=0.5, rely=0.5, anchor='center')

        title_font = tkFont.Font(family="Arial", size=24, weight="bold")
        text_font = tkFont.Font(family="Arial", size=16)

        tk.Label(self.instructions_frame, text=title, font=title_font, bg='white').pack(pady=20)
        tk.Label(self.instructions_frame, text=message, font=text_font, bg='white', wraplength=700, justify="left").pack(pady=20)

        tk.Button(self.instructions_frame, text="OK", font=("Arial", 16), bg='#4CAF50', fg='white',
                  command=lambda: [self.instructions_frame.destroy(), next_function() if next_function else self.practice_session()]).pack(pady=20)

    def setup_game_elements(self):
        self.instructions = tk.Label(self.root, text="", font=("Arial", 24), bg='white')
        self.instructions.place(relx=0.5, rely=0.08, anchor='center')

        self.timer_label = tk.Label(self.root, text="", font=("Arial", 24), fg="red", bg='white')
        self.timer_label.place(relx=0.9, rely=0.08, anchor='center')

        self.score_label = tk.Label(self.root, text="Earnings: $0.00", font=("Arial", 20), bg='white')
        self.score_label.place(relx=0.5, rely=0.15, anchor='center')
        
        self.last_earnings_label = tk.Label(self.root, text="Last Balloon: $0.00", font=("Arial", 14), bg='white', fg='gray')
        self.last_earnings_label.place(relx=0.5, rely=0.19, anchor='center')


        self.balloon_label = tk.Label(self.root, text="", font=("Arial", 20), bg='white')
        self.balloon_label.place(relx=0.5, rely=0.04, anchor='center')

        self.pump_button = tk.Button(self.root, text="Pump", font=("Arial", 20), command=self.pump, bg='#2196F3', fg='white')
        self.pump_button.place(relx=0.4, rely=0.9, anchor='center')

        self.cashout_button = tk.Button(self.root, text="Collect $$$", font=("Arial", 20), command=self.cash_out, bg='#2196F3', fg='white')
        self.cashout_button.place(relx=0.6, rely=0.9, anchor='center')
    
    def get_dynamic_max_balloon_size(self):
        self.root.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Estimate available vertical space between the bottom of top labels and top of buttons
        top_labels_bottom = self.balloon_label.winfo_y() + self.balloon_label.winfo_height()
        bottom_margin = canvas_height - (self.pump_button.winfo_y())  # space below buttons

        usable_height = canvas_height - top_labels_bottom - bottom_margin
        usable_radius = usable_height // 2

        usable_radius = min(usable_radius, canvas_width // 2)
        return usable_radius
    
    # def inflate_to_max_size(self):
    #     if not self.running:
    #         return
    #     self.pumps = self.max_pumps
    #     self.dynamic_max_balloon_size = self.get_dynamic_max_balloon_size()
    #     self.balloon_size = self.dynamic_max_balloon_size
    #     self.draw_balloon()
    #     self.balloon_label.config(text="Max Size Reached (Debug)")

    def practice_session(self):
        self.setup_game_elements()
        self.condition = "practice"
        self.instructions.config(text="Practice Session (Press 'S' to skip)")
        self.trial_number = 0
        self.earnings = 0
        self.update_balloon_label(PRACTICE_ROUNDS)
        self.after_id = self.root.after(1000, self.start_trial, PRACTICE_ROUNDS)

    def skip_practice(self, event=None):
        if self.condition == "practice":
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.clear_game_ui()
            self.trial_number = 0
            self.earnings = 0
            self.start_first_condition()

    def start_first_condition(self):
        if self.participant_info["StartCondition"] == "baseline_first":
            self.start_baseline()
        else:
            self.start_pressure()

    def start_second_condition(self):
        if self.participant_info["StartCondition"] == "baseline_first":
            self.start_pressure()
        else:
            self.start_baseline()


    def start_baseline(self):
        #self.pending_condition = "baseline"
        self.show_instructions(
            "Baseline Round Instructions",
            "In this round, **there is no time limit** — you can take as long as you want for each decision.\n\n"
            "• Each pump adds $0.05 to your potential earnings.\n"
            "• However, the balloon can burst **at any moment without warning**, causing you to lose all earnings for that balloon.\n"
            "• You can click 'Collect $$$' at any time to safely collect your earnings for that balloon.\n\n"
            "Click OK when you're ready to begin.",
            next_function=self._start_baseline
        )


    def _start_baseline(self):
        #self.pending_condition = None
        self.condition = "baseline"
        self.trial_number = 0
        self.earnings = 0
        self.setup_game_elements()
        self.score_label.config(text="Earnings: $0.00")
        self.instructions.config(text="Baseline (No Time Constraint)")
        self.update_balloon_label(BASELINE_ROUNDS)
        self.start_trial(BASELINE_ROUNDS)

    def start_pressure(self):
        #self.pending_condition = None
        #self.pending_condition = "pressure"
        self.show_instructions(
            "Time-Constrained Round Instructions",
            "This round is the same as before, **except now you have only 15 seconds** to decide how much to pump each balloon.\n\n"
            "• Each pump still adds €0.05.\n"
            "• The balloon can still burst **at any moment without warning**, causing you to lose that balloon’s earnings.\n"
            "• You can still click 'Collect $$$' at any time to lock in your current earnings.\n\n"
            "Click OK when you're ready to begin.",
            next_function=self._start_pressure
        )


    def _start_pressure(self):
        self.condition = "pressure"
        self.trial_number = 0
        self.earnings = 0
        self.setup_game_elements()
        self.score_label.config(text="Earnings: $0.00")
        self.instructions.config(text="Time Constraint (15s per Balloon)")
        self.update_balloon_label(PRESSURE_ROUNDS)
        self.start_trial(PRESSURE_ROUNDS)

    def break_screen(self):
        self.clear_game_ui()  # Clears canvas, labels, and buttons
        self.instructions.config(text="Break: Relax for 5 minutes")
        for i in range(BREAK_SECONDS, 0, -1):
            self.timer_label.config(text=f"{i}s")
            self.root.update()
            time.sleep(1)
        self.clear_game_ui()  # Clear all leftover UI elements
        self.start_second_condition()


    def update_balloon_label(self, total_rounds):
        if self.balloon_label:
            self.balloon_label.config(text=f"Balloon {self.trial_number + 1} of {total_rounds}")

    def start_trial(self, total_rounds):
        if self.condition == "break":
            return  # Do nothing during break
        if self.trial_number >= total_rounds:
            # End of current condition
            if self.condition == "practice":
                self.clear_game_ui()
                self.start_first_condition()

            elif self.condition in ["baseline", "pressure"]:
                # Save current earnings to respective variable
                if self.condition == "baseline":
                    self.earnings_baseline = self.earnings
                else:
                    self.earnings_pressure = self.earnings

                self.conditions_completed += 1

                if self.conditions_completed == 1:
                    self.clear_game_ui()
                    self.break_screen()  # only after first real round
                elif self.conditions_completed == 2:
                    self.end_experiment()

            else:
                self.end_experiment()  # catch-all safeguard
            return
        if self.condition == "baseline" or self.condition == "pressure":
            self.explosion_point = self.explosion_points[self.trial_number]
        else:
            # Use default Lejuez-like array for practice
            self.explosion_array = [i for i in range(1, 65)]  # explosion between 1 and 64
            random.shuffle(self.explosion_array)
            self.explosion_point = self.explosion_array[self.trial_number]

        
        self.canvas.delete("all")
        canvas_height = self.canvas.winfo_height()
        canvas_width = self.canvas.winfo_width()
        top_margin = 200
        bottom_margin = 100
        usable_height = canvas_height - top_margin - bottom_margin

        # Dynamically set max balloon size to avoid UI overlap
        self.dynamic_max_balloon_size = self.get_dynamic_max_balloon_size()


        self.balloon_size = BALLOON_ORIGINAL_SIZE
        self.pumps = 0
        self.running = True


        self.draw_balloon()
        self.update_balloon_label(PRACTICE_ROUNDS if self.condition == "practice" else BASELINE_ROUNDS if self.condition == "baseline" else PRESSURE_ROUNDS)

        if self.condition == "pressure":
            self.countdown_start_time = time.time()
            self.update_countdown()         

    def draw_balloon(self):
        self.canvas.delete("balloon")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Allocate space: leave enough margin for labels at top
        top_margin = 200   # space for instructions/labels
        bottom_margin = 100  # space for buttons

        usable_height = height - top_margin - bottom_margin
        max_radius = min(BALLOON_MAX_SIZE, usable_height // 2, width // 2)

        # Draw centered balloon in usable space
        center_x = width / 2
        center_y = top_margin + usable_height / 2

        x0 = center_x - self.balloon_size
        y0 = center_y - self.balloon_size
        x1 = center_x + self.balloon_size
        y1 = center_y + self.balloon_size

        self.balloon = self.canvas.create_oval(x0, y0, x1, y1, fill="lightblue", tags="balloon")

    def calculate_balloon_size(self):
        growth_ratio = self.pumps / 64
        self.balloon_size = BALLOON_ORIGINAL_SIZE + (self.dynamic_max_balloon_size - BALLOON_ORIGINAL_SIZE) * growth_ratio

    def pump(self):
        if not self.running:
            return
        self.pumps += 1
        self.calculate_balloon_size()
        self.draw_balloon()
        if self.pumps >= self.explosion_point:
            self.balloon_pop()

    def cash_out(self):
        if not self.running:
            return
        self.running = False
        amount = self.pumps * 0.05
        self.earnings += amount
        self.score_label.config(text=f"Earnings: ${self.earnings:.2f}")
        self.last_earnings = amount
        self.last_earnings_label.config(text=f"Last Balloon: ${self.last_earnings:.2f}")

        self.save_trial(popped=False)
        self.trial_number += 1
        self.root.after(300, self.start_trial, PRACTICE_ROUNDS if self.condition == "practice" else BASELINE_ROUNDS if self.condition == "baseline" else PRESSURE_ROUNDS)

    def balloon_pop(self):
        self.running = False
        self.canvas.delete("balloon")
        self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2, text="POP!", font=("Arial", 40), fill="red")
        play_pop_sound()
        self.save_trial(popped=True)
        self.trial_number += 1
        self.last_earnings = 0.0
        self.last_earnings_label.config(text=f"Last Balloon: ${self.last_earnings:.2f}")
        self.root.after(300, self.start_trial, PRACTICE_ROUNDS if self.condition == "practice" else BASELINE_ROUNDS if self.condition == "baseline" else PRESSURE_ROUNDS)

    def update_countdown(self):
        if not self.running:
            return

        elapsed = time.time() - self.countdown_start_time
        remaining = max(0, TIME_PRESSURE_SECONDS - int(elapsed))
        self.timer_label.config(text=f"{remaining}s")

        if remaining <= 0:
            self.balloon_pop()
        else:
            self.root.after(250, self.update_countdown)  # Check more frequently


    def save_trial(self, popped):
        try:
            self.supabase.table('responses').insert({
                "participant_id": self.participant_id,
                "trial_number": self.trial_number,
                "max_pumps": self.explosion_point,
                "num_pumps": self.pumps,
                "popped": popped,
                "total_earnings": round(self.earnings, 2),
                "condition": self.condition
            }).execute()
        except Exception as e:
            print(f"Failed to upload trial: {e}")

        with open("data.txt", "a") as f:
            f.write(str({
                "participant_id": self.participant_id,
                "trial_number": self.trial_number,
                "max_pumps": self.explosion_point,
                "num_pumps": self.pumps,
                "popped": popped,
                "total_earnings": round(self.earnings, 2),
                "condition": self.condition
            }) + "\n")

    def end_experiment(self):
        self.clear_game_ui()
        try:
            self.supabase.table('participants').update({"completed": True}).eq("participant_id", self.participant_id).execute()
        except Exception as e:
            print(f"Failed to mark participant as completed: {e}")
        total = self.earnings_baseline + self.earnings_pressure
        final_text = (
            "Thank you for participating!\n\n"
            f"Total Earnings = Baseline (${self.earnings_baseline:.2f}) + "
            f"Time Constraint (${self.earnings_pressure:.2f}) = "
            f"${total:.2f}"
        )
        self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            self.canvas.winfo_height() / 2,
            text=final_text,
            font=("Arial", 24),
            justify="center"
        )   

    def clear_game_ui(self):
        if hasattr(self, 'pump_button'):
            self.pump_button.destroy()
        if hasattr(self, 'cashout_button'):
            self.cashout_button.destroy()
        if hasattr(self, 'score_label'):
            self.score_label.destroy()
        if hasattr(self, 'last_earnings_label'):
            self.last_earnings_label.destroy()

        if hasattr(self, 'balloon_label'):
            self.balloon_label.destroy()
        if hasattr(self, 'timer_label'):
            self.timer_label.config(text="")
        if hasattr(self, 'instructions'):
            self.instructions.config(text="")
        self.canvas.delete("all")


    def debug_skip_all(self, event=None):
        self.debug_mode_enabled = True

        self.participant_id = "99999999"
        self.participant_info = {
            "Age": "99",
            "Major": "DebugMajor",
            "Standing": "Senior",
            "Gender": "Male",
            "Stress Level": "Relaxed",
            "Sleep Hours": "8",
            "Caffeine Today": "No",
            "Caffeine Amount": "0",
            "StartCondition": "baseline_first",
            "participant_id": self.participant_id
        }

        if hasattr(self, "pages"):
            for page in self.pages:
                page.destroy()

        self.conditions_completed = 0
        self.earnings = 0
        self.root.bind('s', self.skip_practice)

        self.show_instructions("Debug Mode Activated", "Starting directly with practice round (press 'S' to skip).")
""" 
    def skip_condition_for_testing(self, event=None):
        if not self.debug_mode_enabled:
            return  # Prevent skipping unless debug mode is active

        # Destroy lingering instruction screen if present
        if hasattr(self, 'instructions_frame') and self.instructions_frame.winfo_exists():
            self.instructions_frame.destroy()

        # Handle pending state (instruction shown, condition not started yet)
        if hasattr(self, 'pending_condition') and self.pending_condition:
            if self.pending_condition == "baseline":
                self.earnings_baseline = 0
                self.conditions_completed += 1
                self.pending_condition = None
                self.clear_game_ui()
                self.break_screen()
                return
            elif self.pending_condition == "pressure":
                self.earnings_pressure = 0
                self.conditions_completed += 1
                self.pending_condition = None
                self.clear_game_ui()
                self.end_experiment()
                return

        # Handle in-progress condition
        if self.condition == "practice":
            self.trial_number = PRACTICE_ROUNDS
            self.start_trial(PRACTICE_ROUNDS)
        elif self.condition == "baseline":
            self.earnings_baseline = self.earnings
            self.trial_number = BASELINE_ROUNDS
            self.start_trial(BASELINE_ROUNDS)
        elif self.condition == "pressure":
            self.earnings_pressure = self.earnings
            self.trial_number = PRESSURE_ROUNDS
            self.start_trial(PRESSURE_ROUNDS)
        elif self.condition == "break":
            if self.break_after_id:
                self.root.after_cancel(self.break_after_id)
                self.break_after_id = None
            self.clear_game_ui()
        self.start_second_condition() """




if __name__ == "__main__":
    root = tk.Tk()
    app = BARTApp(root)
    root.mainloop()
