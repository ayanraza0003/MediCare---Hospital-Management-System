"""Main Tkinter window, navigation and integrated data pages."""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from utils.storage import initialize_storage, load_records, save_records
from services.records import save_entity, delete_entity, patient_record, doctor_record, medicine_record, medicine_warnings, search_records
from services.appointments import save_appointment, set_status
from services.billing import create_bill
from services.analytics import billing_summary, visits_last_days, scipy_summary
from services.health_scraper import fetch_page

NAV = ["Dashboard", "Patients", "Doctors", "Appointments", "Medicine Inventory", "Billing", "Analytics", "Health Explorer"]
SPECS = {
    "Patients": ("patients.json", "P", [("name", "Full name"), ("age", "Age"), ("gender", "Gender"), ("phone", "Phone"), ("email", "Email (optional)"), ("address", "Address (optional)")], ["id", "name", "age", "gender", "phone", "email"], ["id", "name", "phone"]),
    "Doctors": ("doctors.json", "D", [("name", "Full name"), ("specialization", "Specialization"), ("phone", "Phone"), ("fee", "Consultation fee")], ["id", "name", "specialization", "phone", "fee"], ["id", "name", "specialization"]),
    "Medicine Inventory": ("medicines.json", "M", [("name", "Medicine name"), ("category", "Category"), ("quantity", "Available quantity"), ("unit", "Unit / packaging"), ("reorder_level", "Reorder threshold"), ("expiry", "Expiry date (YYYY-MM-DD)"), ("price", "Unit price")], ["id", "name", "category", "quantity", "unit", "reorder_level", "expiry", "price"], ["id", "name", "category"]),
}


class MediCareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        initialize_storage()
        self.title("MediCare | Hospital Management & Analytics")
        self.geometry("1240x780")
        self.minsize(980, 640)
        self.configure(bg="#f3f6fa")
        self._style()
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ttk.Label(self.sidebar, text="✚ MediCare", style="Brand.TLabel").pack(anchor="w", padx=22, pady=(28, 4))
        ttk.Label(self.sidebar, text="HOSPITAL MANAGEMENT", style="SideHint.TLabel").pack(anchor="w", padx=24, pady=(0, 28))
        self.content = ttk.Frame(self, style="Main.TFrame", padding=(28, 24))
        self.content.pack(side="right", fill="both", expand=True)
        for item in NAV:
            ttk.Button(self.sidebar, text=item, style="Nav.TButton", command=lambda page=item: self.show(page)).pack(fill="x", padx=12, pady=3, ipady=7)
        self.status = tk.StringVar(value="Ready · Local demo data")
        ttk.Label(self, textvariable=self.status, style="Status.TLabel", anchor="w", padding=(12, 5)).pack(side="bottom", fill="x")
        self.show("Dashboard")

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Sidebar.TFrame", background="#12233f")
        style.configure("Brand.TLabel", background="#12233f", foreground="white", font=("Segoe UI", 19, "bold"))
        style.configure("SideHint.TLabel", background="#12233f", foreground="#9fb1ca", font=("Segoe UI", 8, "bold"))
        style.configure("Nav.TButton", background="#12233f", foreground="#dbe6f4", borderwidth=0, anchor="w", font=("Segoe UI", 10))
        style.map("Nav.TButton", background=[("active", "#23466f")], foreground=[("active", "white")])
        style.configure("Main.TFrame", background="#f3f6fa")
        style.configure("Title.TLabel", background="#f3f6fa", foreground="#162b4d", font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", background="#f3f6fa", foreground="#63748b", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="white", relief="solid", borderwidth=1)
        style.configure("CardLabel.TLabel", background="white", foreground="#687b93", font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background="white", foreground="#18345a", font=("Segoe UI", 21, "bold"))
        style.configure("Status.TLabel", background="#e5ebf2", foreground="#53657b", font=("Segoe UI", 9))
        style.configure("Treeview", rowheight=29, font=("Segoe UI", 9), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e8eef5", foreground="#233b5d")
        style.configure("Accent.TButton", background="#1d6db5", foreground="white", font=("Segoe UI", 9, "bold"), padding=(12, 7))
        style.map("Accent.TButton", background=[("active", "#15548e")])

    def show(self, page):
        for child in self.content.winfo_children():
            child.destroy()
        self.status.set(f"{page} · Local records are stored on this computer")
        if page == "Dashboard": self.dashboard()
        elif page in SPECS: self.entity_page(page)
        elif page == "Appointments": self.appointments_page()
        elif page == "Billing": self.billing_page()
        elif page == "Analytics": self.analytics_page()
        else: self.health_page()

    def heading(self, title, subtitle):
        ttk.Label(self.content, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.content, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(3, 20))

    def dashboard(self):
        self.heading("Dashboard", "A clear snapshot of hospital administration activity.")
        try:
            patients, doctors = load_records("patients.json"), load_records("doctors.json")
            appointments, medicines, bills = (load_records(file) for file in ("appointments.json", "medicines.json", "bills.json"))
            from datetime import datetime
            now = datetime.now()
            upcoming = [row for row in appointments if row.get("status") == "Booked" and (row.get("date", "") > now.date().isoformat() or (row.get("date") == now.date().isoformat() and row.get("time", "") > now.strftime("%H:%M")))]
            attention = sum(bool(medicine_warnings(row)) for row in medicines)
            revenue = sum(float(row.get("total", 0)) for row in bills)
        except (OSError, ValueError) as error:
            messagebox.showerror("Data unavailable", str(error)); return
        grid = ttk.Frame(self.content, style="Main.TFrame"); grid.pack(fill="x")
        cards = [("TOTAL PATIENTS", len(patients)), ("TOTAL DOCTORS", len(doctors)), ("UPCOMING BOOKINGS", len(upcoming)), ("MEDICINES NEEDING ATTENTION", attention), ("RECORDED REVENUE", f"₹{revenue:,.2f}")]
        for index, (label, value) in enumerate(cards):
            card = ttk.Frame(grid, style="Card.TFrame", padding=17); card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=6, pady=6)
            ttk.Label(card, text=label, style="CardLabel.TLabel").pack(anchor="w")
            ttk.Label(card, text=str(value), style="CardValue.TLabel").pack(anchor="w", pady=(6, 0))
            grid.columnconfigure(index % 3, weight=1)
        ttk.Label(self.content, text="Upcoming appointments", font=("Segoe UI", 13, "bold"), background="#f3f6fa", foreground="#18345a").pack(anchor="w", pady=(24, 8))
        upcoming.sort(key=lambda row: (row.get("date", ""), row.get("time", "")))
        for row in upcoming[:6]:
            patient = next((p.get("name") for p in patients if p.get("id") == row.get("patient_id")), "Unknown patient")
            doctor = next((d.get("name") for d in doctors if d.get("id") == row.get("doctor_id")), "Unknown doctor")
            ttk.Label(self.content, text=f"{row.get('date')}  {row.get('time')}     {patient}  ·  {doctor}", background="#f3f6fa").pack(anchor="w", pady=3)
        if not upcoming: ttk.Label(self.content, text="No upcoming bookings yet. Add a patient, doctor and appointment to get started.", background="#f3f6fa").pack(anchor="w")

    def entity_page(self, page):
        filename, prefix, fields, columns, searchable = SPECS[page]
        self.heading(page, "Manage records, use Search to narrow the list, and select a row to edit it.")
        toolbar = ttk.Frame(self.content); toolbar.pack(fill="x", pady=(0, 10))
        query = tk.StringVar()
        ttk.Entry(toolbar, textvariable=query, width=32).pack(side="left", padx=(0, 7))
        ttk.Button(toolbar, text="Search", command=lambda: fill()).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Refresh", command=lambda: fill()).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Add New", style="Accent.TButton", command=lambda: edit_form()).pack(side="right", padx=3)
        ttk.Button(toolbar, text="Edit Selected", command=lambda: selected_edit()).pack(side="right", padx=3)
        ttk.Button(toolbar, text="Delete Selected", command=lambda: delete_selected()).pack(side="right", padx=3)
        frame = ttk.Frame(self.content); frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title()); tree.column(col, width=115, anchor="w")
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=ybar.set)
        tree.pack(side="left", fill="both", expand=True); ybar.pack(side="right", fill="y")
        def fill():
            try:
                rows = search_records(filename, query.get(), searchable)
                tree.delete(*tree.get_children())
                for row in rows:
                    values = [row.get(col, "") for col in columns]
                    if page == "Medicine Inventory": values.append(", ".join(medicine_warnings(row)) or "OK")
                    tree.insert("", "end", iid=row["id"], values=values)
            except (OSError, ValueError) as error: messagebox.showerror("Could not load records", str(error))
        if page == "Medicine Inventory":
            tree["columns"] = (*columns, "warnings"); tree.heading("warnings", text="Warnings"); tree.column("warnings", width=180)
        def view_details(_event=None):
            selection = tree.selection()
            if not selection: return
            record = next((row for row in load_records(filename) if row.get("id") == selection[0]), None)
            if record:
                details = "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in record.items())
                messagebox.showinfo(f"{page} details", details)
        tree.bind("<Double-1>", view_details)
        def selected():
            selection = tree.selection()
            if not selection: raise ValueError("Select a record first.")
            return selection[0]
        def edit_form(record_id=None):
            existing = next((r for r in load_records(filename) if r.get("id") == record_id), {}) if record_id else {}
            dialog = tk.Toplevel(self); dialog.title(f"{'Edit' if record_id else 'Add'} {page[:-1] if page != 'Medicine Inventory' else 'Medicine'}"); dialog.transient(self); dialog.grab_set()
            entries = {}
            for idx, (key, label) in enumerate(fields):
                ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="w", padx=12, pady=5)
                value = tk.StringVar(value=str(existing.get(key, "")))
                widget = ttk.Entry(dialog, textvariable=value, width=36)
                if key == "gender": widget = ttk.Combobox(dialog, textvariable=value, values=("Female", "Male", "Non-binary", "Prefer not to say"), state="readonly", width=33)
                widget.grid(row=idx, column=1, sticky="ew", padx=12, pady=5); entries[key] = value
            def save():
                try:
                    raw = {key: value.get() for key, value in entries.items()}
                    validated = patient_record(raw) if page == "Patients" else doctor_record(raw) if page == "Doctors" else medicine_record(raw)
                    save_entity(filename, prefix, validated, record_id)
                except (OSError, ValueError) as error: messagebox.showerror("Check the form", str(error), parent=dialog); return
                dialog.destroy(); fill(); self.status.set(f"{page[:-1]} saved")
            buttons = ttk.Frame(dialog); buttons.grid(row=len(fields), column=0, columnspan=2, pady=12)
            ttk.Button(buttons, text="Save", style="Accent.TButton", command=save).pack(side="left", padx=5); ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
            dialog.resizable(False, False)
        def selected_edit():
            try: edit_form(selected())
            except ValueError as error: messagebox.showinfo("Select a record", str(error))
        def delete_selected():
            try: record_id = selected()
            except ValueError as error: messagebox.showinfo("Select a record", str(error)); return
            if not messagebox.askyesno("Confirm deletion", "Delete the selected record? This cannot be undone."): return
            try:
                protected = (("appointments.json", "patient_id"), ("bills.json", "patient_id")) if page == "Patients" else (("appointments.json", "doctor_id"),) if page == "Doctors" else ()
                delete_entity(filename, record_id, protected)
                fill()
            except (OSError, ValueError) as error: messagebox.showerror("Cannot delete record", str(error))
        fill()

    def appointments_page(self):
        self.heading("Appointments", "Book future visits, reschedule, complete or cancel existing appointments.")
        toolbar = ttk.Frame(self.content); toolbar.pack(fill="x", pady=(0, 10))
        query = tk.StringVar(); ttk.Entry(toolbar, textvariable=query, width=30).pack(side="left", padx=(0, 7))
        tree = ttk.Treeview(self.content, columns=("id", "date", "time", "patient", "doctor", "reason", "status"), show="headings")
        for col in tree["columns"]: tree.heading(col, text=col.title()); tree.column(col, width=125)
        tree.pack(fill="both", expand=True)
        def fill():
            try:
                patients, doctors = load_records("patients.json"), load_records("doctors.json")
                rows = load_records("appointments.json"); q = query.get().casefold()
                tree.delete(*tree.get_children())
                for row in rows:
                    patient = next((p.get("name", "") for p in patients if p["id"] == row.get("patient_id")), "Unknown")
                    doctor = next((d.get("name", "") for d in doctors if d["id"] == row.get("doctor_id")), "Unknown")
                    if q and q not in " ".join(map(str, row.values())).casefold() + patient.casefold() + doctor.casefold(): continue
                    tree.insert("", "end", iid=row["id"], values=(row["id"], row["date"], row["time"], patient, doctor, row.get("reason", ""), row["status"]))
            except (OSError, ValueError) as error: messagebox.showerror("Could not load appointments", str(error))
        ttk.Button(toolbar, text="Search", command=fill).pack(side="left"); ttk.Button(toolbar, text="Refresh", command=fill).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Book Appointment", style="Accent.TButton", command=lambda: form()).pack(side="right")
        controls = ttk.Frame(self.content); controls.pack(fill="x", pady=8)
        def current_id():
            sel = tree.selection()
            if not sel: raise ValueError("Select an appointment first.")
            return sel[0]
        def form(appointment_id=None):
            patients, doctors = load_records("patients.json"), load_records("doctors.json")
            if not patients or not doctors: messagebox.showinfo("Records needed", "Add at least one patient and one doctor before booking."); return
            existing = next((row for row in load_records("appointments.json") if row["id"] == appointment_id), {}) if appointment_id else {}
            dialog = tk.Toplevel(self); dialog.title("Book or reschedule appointment"); dialog.transient(self); dialog.grab_set()
            patient_map = {f"{p['id']} — {p['name']}": p["id"] for p in patients}; doctor_map = {f"{d['id']} — {d['name']} ({d.get('specialization','')})": d["id"] for d in doctors}
            vals = {"patient_id": tk.StringVar(), "doctor_id": tk.StringVar(), "date": tk.StringVar(value=existing.get("date", "")), "time": tk.StringVar(value=existing.get("time", "")), "reason": tk.StringVar(value=existing.get("reason", "")), "status": tk.StringVar(value=existing.get("status", "Booked"))}
            for idx, (key, label) in enumerate((("patient_id", "Patient"), ("doctor_id", "Doctor"), ("date", "Date YYYY-MM-DD"), ("time", "Time HH:MM"), ("reason", "Reason (optional)"), ("status", "Status"))):
                ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="w", padx=12, pady=5)
                variable = vals[key]
                if key == "patient_id": widget = ttk.Combobox(dialog, textvariable=variable, values=list(patient_map), state="readonly", width=35); variable.set(next((x for x, ident in patient_map.items() if ident == existing.get(key)), ""))
                elif key == "doctor_id": widget = ttk.Combobox(dialog, textvariable=variable, values=list(doctor_map), state="readonly", width=35); variable.set(next((x for x, ident in doctor_map.items() if ident == existing.get(key)), ""))
                elif key == "status": widget = ttk.Combobox(dialog, textvariable=variable, values=("Booked", "Completed", "Cancelled"), state="readonly", width=33)
                else: widget = ttk.Entry(dialog, textvariable=variable, width=38)
                widget.grid(row=idx, column=1, padx=12, pady=5)
            def save():
                data = {key: val.get() for key, val in vals.items()}
                data["patient_id"] = patient_map.get(data["patient_id"]); data["doctor_id"] = doctor_map.get(data["doctor_id"])
                try: save_appointment(data, appointment_id)
                except (OSError, ValueError) as error: messagebox.showerror("Check appointment", str(error), parent=dialog); return
                dialog.destroy(); fill()
            ttk.Button(dialog, text="Save", style="Accent.TButton", command=save).grid(row=6, column=0, pady=12); ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=6, column=1, pady=12)
        ttk.Button(controls, text="Edit / Reschedule", command=lambda: action(lambda ident: form(ident))).pack(side="left", padx=3)
        ttk.Button(controls, text="Mark Completed", command=lambda: action(lambda ident: set_status(ident, "Completed"), "Mark this appointment completed?")).pack(side="left", padx=3)
        ttk.Button(controls, text="Cancel Appointment", command=lambda: action(lambda ident: set_status(ident, "Cancelled"), "Cancel this appointment?")).pack(side="left", padx=3)
        def action(callback, confirmation):
            try:
                ident = current_id()
                if not messagebox.askyesno("Confirm appointment change", confirmation): return
                callback(ident); fill()
            except (OSError, ValueError) as error: messagebox.showerror("Appointment", str(error))
        fill()

    def billing_page(self):
        self.heading("Billing", "Build bills from saved patients, optional doctor details and multiple line items.")
        top = ttk.Frame(self.content); top.pack(fill="x", pady=(0, 10))
        q = tk.StringVar(); ttk.Entry(top, textvariable=q, width=28).pack(side="left", padx=(0, 6))
        tree = ttk.Treeview(self.content, columns=("id", "date", "patient", "total"), show="headings", height=9)
        for col in tree["columns"]: tree.heading(col, text=col.title()); tree.column(col, width=150)
        tree.pack(fill="x")
        details = tk.Text(self.content, height=7, wrap="word", state="disabled"); details.pack(fill="both", expand=True, pady=8)
        def fill():
            try:
                patients = load_records("patients.json"); rows = load_records("bills.json"); query=q.get().casefold(); tree.delete(*tree.get_children())
                for row in rows:
                    name = next((p["name"] for p in patients if p["id"] == row.get("patient_id")), "Unknown")
                    if query and query not in (row["id"] + name).casefold(): continue
                    tree.insert("", "end", iid=row["id"], values=(row["id"], row["date"], name, f"₹{float(row['total']):.2f}"))
            except (OSError, ValueError) as error: messagebox.showerror("Billing", str(error))
        def show_bill(_event=None):
            if not tree.selection(): return
            row = next((b for b in load_records("bills.json") if b["id"] == tree.selection()[0]), None)
            if not row: return
            details.configure(state="normal"); details.delete("1.0", "end")
            details.insert("end", f"Bill {row['id']} · {row['date']}\n" + "\n".join(f"{item['description']}   ₹{float(item['amount']):.2f}" for item in row["items"]) + f"\n\nTotal: ₹{float(row['total']):.2f}")
            details.configure(state="disabled")
        tree.bind("<<TreeviewSelect>>", show_bill)
        ttk.Button(top, text="Search", command=fill).pack(side="left"); ttk.Button(top, text="Refresh", command=fill).pack(side="left", padx=5)
        ttk.Button(top, text="Create Bill", style="Accent.TButton", command=lambda: form()).pack(side="right")
        def form():
            patients, doctors = load_records("patients.json"), load_records("doctors.json")
            if not patients: messagebox.showinfo("Records needed", "Register a patient before creating a bill."); return
            dialog=tk.Toplevel(self); dialog.title("Create bill"); dialog.transient(self); dialog.grab_set()
            patient_map={f"{p['id']} — {p['name']}":p["id"] for p in patients}; doctor_map={"No doctor": "", **{f"{d['id']} — {d['name']}":d["id"] for d in doctors}}
            pv=tk.StringVar(value=next(iter(patient_map))); dv=tk.StringVar(value="No doctor"); dvprev=[""]
            ttk.Label(dialog,text="Patient").grid(row=0,column=0,padx=10,pady=6); ttk.Combobox(dialog,textvariable=pv,values=list(patient_map),state="readonly",width=35).grid(row=0,column=1,padx=10,pady=6)
            ttk.Label(dialog,text="Doctor (optional)").grid(row=1,column=0,padx=10,pady=6); dc=ttk.Combobox(dialog,textvariable=dv,values=list(doctor_map),state="readonly",width=35); dc.grid(row=1,column=1,padx=10,pady=6)
            ttk.Label(dialog,text="Bill date").grid(row=2,column=0,padx=10,pady=6); billdate=tk.StringVar(value=date.today().isoformat()); ttk.Entry(dialog,textvariable=billdate,width=38).grid(row=2,column=1,padx=10,pady=6)
            desc=tk.StringVar(); amt=tk.StringVar(); items=[]
            ttk.Label(dialog,text="Description").grid(row=3,column=0,padx=10,pady=6); ttk.Entry(dialog,textvariable=desc,width=38).grid(row=3,column=1,padx=10,pady=6)
            ttk.Label(dialog,text="Amount").grid(row=4,column=0,padx=10,pady=6); ttk.Entry(dialog,textvariable=amt,width=38).grid(row=4,column=1,padx=10,pady=6)
            itemtree=ttk.Treeview(dialog,columns=("description","amount"),show="headings",height=5); itemtree.heading("description",text="Item"); itemtree.heading("amount",text="Amount"); itemtree.grid(row=5,column=0,columnspan=2,padx=10,pady=5,sticky="ew")
            total=tk.StringVar(value="Total: ₹0.00"); ttk.Label(dialog,textvariable=total,font=("Segoe UI",11,"bold")).grid(row=7,column=0,columnspan=2,pady=5)
            def redraw():
                itemtree.delete(*itemtree.get_children()); value=0
                for idx,item in enumerate(items): itemtree.insert("","end",iid=str(idx),values=(item["description"],f"₹{item['amount']:.2f}")); value+=item["amount"]
                total.set(f"Total: ₹{value:.2f}")
            def add_item():
                if not desc.get().strip(): messagebox.showerror("Bill item","Enter an item description.",parent=dialog); return
                try:
                    from utils.validators import money
                    value=money(amt.get(),"Item amount")
                except ValueError as error: messagebox.showerror("Bill item",str(error),parent=dialog); return
                items.append({"description":desc.get().strip(),"amount":value}); desc.set(""); amt.set(""); redraw()
            def remove_item():
                if itemtree.selection(): items.pop(int(itemtree.selection()[0])); redraw()
            def doctor_changed(_event):
                chosen=doctor_map.get(dv.get(),"")
                doctor=next((d for d in doctors if d["id"]==chosen),None)
                if doctor and chosen!=dvprev[0] and not any(i["description"]=="Consultation fee" for i in items):
                    items.append({"description":"Consultation fee","amount":float(doctor.get("fee",0))}); redraw()
                dvprev[0]=chosen
            dc.bind("<<ComboboxSelected>>",doctor_changed)
            ttk.Button(dialog,text="Add Item",command=add_item).grid(row=6,column=0,pady=5); ttk.Button(dialog,text="Remove Selected",command=remove_item).grid(row=6,column=1,pady=5)
            def save():
                try: create_bill(patient_map[pv.get()],doctor_map.get(dv.get(),""),billdate.get(),items)
                except (OSError,ValueError) as error: messagebox.showerror("Could not save bill",str(error),parent=dialog); return
                dialog.destroy(); fill()
            ttk.Button(dialog,text="Save Bill",style="Accent.TButton",command=save).grid(row=8,column=0,pady=12); ttk.Button(dialog,text="Cancel",command=dialog.destroy).grid(row=8,column=1,pady=12)
        fill()

    def analytics_page(self):
        self.heading("Analytics", "Operational summaries from local bills and completed appointments.")
        try:
            summary=billing_summary(); labels, counts=visits_last_days(); stats=scipy_summary(counts)
        except (OSError, ValueError, ImportError) as error:
            messagebox.showerror("Analytics unavailable", f"{error}\nInstall project requirements to use analytics."); return
        row=ttk.Frame(self.content); row.pack(fill="x")
        for label,value in (("Bills",summary["count"]),("Revenue",f"₹{summary['total']:.2f}"),("Average bill",f"₹{summary['mean']:.2f}"),("Lowest / highest",f"₹{summary['minimum']:.2f} / ₹{summary['maximum']:.2f}")):
            ttk.Label(row,text=f"{label}: {value}",font=("Segoe UI",10,"bold"),background="white",padding=12).pack(side="left",fill="x",expand=True,padx=4)
        if stats:
            txt=f"SciPy daily completed-visit statistics (last 30 days): {stats['observations']} observations · minimum {stats['minimum']:.0f} · maximum {stats['maximum']:.0f} · mean {stats['mean']:.2f} · variance {stats['variance']:.2f}"
        else: txt="SciPy daily visit statistics need at least two daily observations. Additional calendar days provide meaningful variance."
        ttk.Label(self.content,text=txt,background="#e8f1fb",foreground="#244b73",wraplength=900,padding=10).pack(fill="x",pady=12)
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            ttk.Label(self.content,text="Charts require Matplotlib. Install the dependencies listed in requirements.txt.",background="#f3f6fa").pack(anchor="w"); return
        bills=load_records("bills.json"); revenue={}
        for bill in bills: revenue[bill.get("date","")]=revenue.get(bill.get("date",""),0)+float(bill.get("total",0))
        fig=Figure(figsize=(10,4.2),dpi=100); ax1=fig.add_subplot(121); ax2=fig.add_subplot(122)
        ax1.plot([d.strftime("%m-%d") for d in labels],counts,color="#1976b9",marker="o",markersize=3); ax1.set_title("Completed visits · last 30 days"); ax1.set_ylabel("Visits"); ax1.tick_params(axis="x",labelrotation=60,labelsize=7); ax1.grid(alpha=.2)
        dates=sorted(revenue); ax2.bar(dates,[revenue[d] for d in dates],color="#3a9b83"); ax2.set_title("Billing revenue by date"); ax2.set_ylabel("Amount"); ax2.tick_params(axis="x",labelrotation=60,labelsize=7); ax2.grid(axis="y",alpha=.2)
        fig.tight_layout(); canvas=FigureCanvasTkAgg(fig,master=self.content); canvas.draw(); canvas.get_tk_widget().pack(fill="both",expand=True)
        ttk.Button(self.content,text="Refresh Analytics",command=lambda:self.show("Analytics")).pack(anchor="e",pady=5)

    def health_page(self):
        self.heading("Health Explorer", "Fetch and summarize one public health information page.")
        url=tk.StringVar(value="https://www.who.int/health-topics"); ttk.Label(self.content,text="HTTPS page URL",background="#f3f6fa").pack(anchor="w")
        bar=ttk.Frame(self.content); bar.pack(fill="x",pady=7); ttk.Entry(bar,textvariable=url).pack(side="left",fill="x",expand=True,padx=(0,8))
        result=tk.Text(self.content,wrap="word",height=26); result.pack(fill="both",expand=True,pady=8)
        status=tk.StringVar(value="Informational content only; not a substitute for professional medical advice."); ttk.Label(self.content,textvariable=status,background="#f3f6fa",foreground="#566a80",wraplength=900).pack(anchor="w")
        button=ttk.Button(bar,text="Fetch Information",style="Accent.TButton"); button.pack(side="right")
        def fetch():
            target_url = url.get()
            button.configure(state="disabled"); status.set("Fetching page in the background…")
            def worker():
                try: data=fetch_page(target_url); error=None
                except (ValueError, OSError) as exc: data=None; error=str(exc)
                def finish():
                    button.configure(state="normal"); result.delete("1.0","end")
                    if error: status.set("The page could not be loaded."); result.insert("end",error); return
                    status.set(f"Source: {data['source']} · Informational only; not medical advice.")
                    result.insert("end",f"{data['title']}\n\nHeadings\n"+("\n".join("• "+x for x in data["headings"]) or "No headings found.")+"\n\nLinks\n"+("\n".join(f"• {x['title']} — {x['url']}" for x in data["links"][:20]) or "No links found.")+"\n\nReadable text\n"+"\n\n".join(data["paragraphs"][:8]))
                self.after(0,finish)
            threading.Thread(target=worker,daemon=True).start()
        button.configure(command=fetch)
