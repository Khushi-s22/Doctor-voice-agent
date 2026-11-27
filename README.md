# NexovAI – Voice AI Doctor Appointment Assistant

NexovAI is a real-time voice-based AI doctor appointment assistant that helps patients check doctor availability, book appointments, and cancel existing appointments through natural voice conversations.

The application combines a Python-based voice pipeline with a React dashboard to provide an interactive appointment booking experience.

## Features

- Real-time voice conversations with an AI assistant.
- Speech-to-Text (STT) using ElevenLabs.
- AI-powered responses using Groq LLM.
- Text-to-Speech (TTS) using ElevenLabs.
- Check doctor availability and appointment slots.
- Book appointments through voice commands.
- Cancel existing appointments using the patient's spoken phone number.
- Phone number confirmation before booking or cancellation.
- Live conversation transcript.
- Dashboard displaying available doctors and appointments.
- WebRTC-based browser audio communication.

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Voice Framework | Pipecat |
| Frontend | React, Vite |
| Speech-to-Text | ElevenLabs |
| Text-to-Speech | ElevenLabs |
| LLM | Groq |
| Real-time Communication | WebRTC |
| Data Storage | JSON files |

## Voice Pipeline Architecture

The application follows this voice processing pipeline:

**Patient Audio → WebRTC → ElevenLabs STT → Groq LLM → Appointment Tools → ElevenLabs TTS → WebRTC → Patient Audio**

The AI assistant can call three appointment tools:

1. `check_doctor_availability` – Checks available doctors and appointment slots.
2. `book_appointment` – Books an appointment using the patient's confirmed phone number.
3. `cancel_appointment` – Cancels an existing appointment using the confirmed phone number.

## Project Structure

```text
Doctor-voice-agent/
│
├── backend/
│   ├── data/
│   │   ├── doctors.json
│   │   └── appointments.json
│   │
│   ├── tools/
│   │   └── appointment_tools.py
│   │
│   ├── main.py
│   ├── voice_agent.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   └── package.json
│
├── .gitignore
└── README.md
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Khushi-s22/Doctor-voice-agent.git
cd Doctor-voice-agent
```

### 2. Backend Setup

Open a terminal:

```bash
cd backend

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file inside the backend folder using `.env.example` as a reference.

Add your API credentials:

```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_elevenlabs_voice_id
GROQ_API_KEY=your_groq_api_key
```

Start the backend:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend health check:

```text
http://localhost:8000/health
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Open the application:

```text
http://localhost:5173
```

Allow microphone access when prompted by the browser.

## Appointment Workflow

### Booking

1. The AI assistant greets the patient.
2. It asks for the patient's name and required medical speciality.
3. It checks doctor availability.
4. The patient selects a doctor and appointment slot.
5. The assistant asks for the phone number.
6. It repeats the complete number digit by digit.
7. The patient explicitly confirms the number.
8. The appointment is booked only after confirmation.

### Cancellation

1. The assistant asks for the patient's phone number.
2. It repeats the number and asks for confirmation.
3. It identifies the appointment to cancel.
4. It cancels the appointment after the required confirmation.

## Data Storage

Doctor information and appointments are maintained using JSON files. Available slots are updated when appointments are booked or cancelled.

## Security

- API credentials are stored in environment variables.
- `.env` files are excluded from Git.
- `.env.example` contains placeholder values only.
- The assistant does not use login, OTP, or caller ID for patient identification.

## Future Improvements

- Phone-style call interface.
- Live audio waveform visualization.
- Call timer and mute controls.
- Enhanced appointment confirmation UI.
- Persistent database integration.

## Author

**Khushi**

GitHub: https://github.com/Khushi-s22

