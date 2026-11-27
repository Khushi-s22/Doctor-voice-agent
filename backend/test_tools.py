
from tools.appointment_tools import (
    check_doctor_availability,
    book_appointment,
    cancel_appointment
)

# 1. Check availability
print("\n--- CHECK AVAILABILITY ---")
result = check_doctor_availability("Cardiologist")
print(result)

# 2. Book appointment
print("\n--- BOOK APPOINTMENT ---")
booking = book_appointment(
    patient_name="Khushi",
    phone_number="9876543210",
    doctor_name="Dr. Ananya Sharma",
    appointment_slot="2026-11-25 10:00 AM"
)
print(booking)

# 3. Cancel appointment
print("\n--- CANCEL APPOINTMENT ---")
cancellation = cancel_appointment(
    doctor_name="Dr. Ananya Sharma",
    appointment_slot="2026-11-25 10:00 AM"
)
print(cancellation)
