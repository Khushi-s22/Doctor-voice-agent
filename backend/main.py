import asyncio
import json
import logging
from pathlib import Path
from tools.appointment_tools import check_doctor_availability
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCRequestHandler,
    SmallWebRTCRequest,
    SmallWebRTCPatchRequest,
    IceCandidate,
)

from voice_agent import run_bot


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Doctor Voice Agent API")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

webrtc_handler = SmallWebRTCRequestHandler()

# Keep active voice tasks alive while calls are running.
bot_tasks = set()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    return {
        "message": "Doctor Voice Agent Backend is running!"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/doctors")
async def get_doctors():
    specialities = [
        "Cardiologist",
        "Dermatologist",
        "Neurologist"
    ]

    doctors = []

    for speciality in specialities:
        result = check_doctor_availability(speciality)

        if "doctors" in result:
            doctors.extend([
                {
                    "name": doctor["doctor"],
                    "speciality": doctor["speciality"],
                    "available_slots": doctor["available_slots"]
                }
                for doctor in result.get("doctors", [])
            ])

    return {"doctors": doctors}

@app.get("/api/appointments")
async def get_appointments():
    appointments_file = DATA_DIR / "appointments.json"

    if not appointments_file.exists():
        return {"appointments": []}

    with open(appointments_file, "r", encoding="utf-8") as file:
        appointments = json.load(file)

    return {"appointments": appointments}


def on_bot_finished(task):
    bot_tasks.discard(task)

    if task.cancelled():
        return

    error = task.exception()
    if error:
        logger.error(
            "Voice bot task failed: %s",
            error,
            exc_info=error,
        )


@app.post("/api/offer")
async def handle_offer(request: Request):
    try:
        payload = await request.json()
        webrtc_request = SmallWebRTCRequest(**payload)

        async def start_voice_bot(connection):
            task = asyncio.create_task(run_bot(connection))
            bot_tasks.add(task)
            task.add_done_callback(on_bot_finished)

        answer = await webrtc_handler.handle_web_request(
            webrtc_request,
            start_voice_bot,
        )

        return answer

    except Exception as error:
        logger.exception("WebRTC offer failed")
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.patch("/api/offer")
async def handle_ice_candidates(request: Request):
    try:
        payload = await request.json()

        patch_request = SmallWebRTCPatchRequest(
            pc_id=payload["pc_id"],
            candidates=[
                IceCandidate(**candidate)
                for candidate in payload.get("candidates", [])
            ],
        )

        await webrtc_handler.handle_patch_request(patch_request)

        return {"status": "ok"}

    except Exception as error:
        logger.exception("ICE candidate processing failed")
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
