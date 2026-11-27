
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "doctors.json"
)

APPOINTMENTS_FILE = os.path.join(
    os.path.dirname(DATA_FILE),
    "appointments.json"
)


def load_doctors():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        doctors = json.load(file)

    # Preserve original daily appointment times
    # so booked slots are not lost during regeneration.
    changed = False

    for doctor in doctors:
        if "slot_times" not in doctor:
            doctor["slot_times"] = []

            for slot in doctor.get("available_slots", []):
                try:
                    slot_time = datetime.strptime(
                        slot, "%Y-%m-%d %I:%M %p"
                    ).strftime("%I:%M %p")

                    if slot_time not in doctor["slot_times"]:
                        doctor["slot_times"].append(slot_time)
                except ValueError:
                    continue

            changed = True

    if changed:
        save_doctors(doctors)

    return doctors


def save_doctors(doctors):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(doctors, file, indent=4)


def load_appointments():
    if not os.path.exists(APPOINTMENTS_FILE):
        return []

    with open(APPOINTMENTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_appointments(appointments):
    with open(APPOINTMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(appointments, file, indent=4)


def get_available_slots(doctor, appointments):
    available = []
    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    # Generate slots for today and the next 6 days.
    for day in range(7):
        appointment_date = (now + timedelta(days=day)).date()

        for slot_time in doctor["slot_times"]:
            slot = datetime.strptime(
                f"{appointment_date} {slot_time}",
                "%Y-%m-%d %I:%M %p"
            ).replace(tzinfo=now.tzinfo)
            
            if slot <= now:
                continue

            already_booked = any(
                appointment["doctor_name"].lower() == doctor["name"].lower()
                and appointment["appointment_slot"] == slot.strftime(
                    "%Y-%m-%d %I:%M %p"
                )
                for appointment in appointments
            )

            if not already_booked:
                available.append(
                    slot.strftime("%Y-%m-%d %I:%M %p")
                )

    return available


# Tool 1: Check doctor availability
def check_doctor_availability(speciality: str):
    doctors = load_doctors()
    appointments = load_appointments()
    results = []

    for doctor in doctors:
        if speciality.lower() in doctor["speciality"].lower():
            slots = get_available_slots(doctor, appointments)

            results.append({
                "doctor": doctor["name"],
                "speciality": doctor["speciality"],
                "available_slots": slots
            })

    if not results:
        return {"message": "No doctors found for this speciality."}

    return {"doctors": results}


# Tool 2: Book appointment
def book_appointment(
    patient_name: str,
    phone_number: str,
    doctor_name: str,
    appointment_slot: str
):
    doctors = load_doctors()
    appointments = load_appointments()

    for doctor in doctors:
        if doctor["name"].lower() == doctor_name.lower():

            available_slots = get_available_slots(
                doctor, appointments
            )

            if appointment_slot not in available_slots:
                return {
                    "error": "This appointment slot is not available."
                }

            appointment = {
                "patient_name": patient_name,
                "phone_number": phone_number,
                "doctor_name": doctor["name"],
                "speciality": doctor["speciality"],
                "appointment_slot": appointment_slot
            }

            appointments.append(appointment)
            save_appointments(appointments)

            return {
                "message": "Appointment booked successfully.",
                "appointment": appointment
            }

    return {"error": "Doctor not found."}


# Tool 3: Cancel appointment
def cancel_appointment(doctor_name: str, appointment_slot: str):
    appointments = load_appointments()

    def normalize_name(name):
        name = name.lower().strip()
        name = name.removeprefix("dr.").strip()
        return " ".join(name.split())

    for index, appointment in enumerate(appointments):
        if (
            normalize_name(appointment["doctor_name"])
            == normalize_name(doctor_name)
            and appointment["appointment_slot"].strip()
            == appointment_slot.strip()
        ):
            appointments.pop(index)
            save_appointments(appointments)

            return {
                "message": "Appointment cancelled successfully."
            }

    return {"error": "Matching appointment not found."}