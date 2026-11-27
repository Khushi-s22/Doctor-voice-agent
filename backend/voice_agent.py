import aiohttp

from config import GROQ_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
from pipecat.audio.vad.silero import SileroVADAnalyzer

from tools.appointment_tools import (
    check_doctor_availability as availability_tool,
    book_appointment as booking_tool,
    cancel_appointment as cancellation_tool,
)

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker, PipelineParams
from pipecat.workers.runner import WorkerRunner

from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

from pipecat.adapters.llm.schemas.function_schema import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams

from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.frames.frames import LLMRunFrame



SYSTEM_PROMPT = """
You are a friendly and professional AI doctor appointment assistant for NexovAI.

GREETING:
- As soon as the call starts, greet the patient first.
- Say: "Hello! Welcome to NexovAI. I'm your AI Doctor Appointment Assistant. How may I help you today?"
- Then wait for the patient to respond.
- Do not start asking booking questions until the patient tells you what they need.

BOOKING:
1. First ask the patient which medical speciality they need.
2. Never assume or automatically select a speciality.
3. Available specialities are Cardiologist, Dermatologist, and Neurologist.
4. If the patient says they want to book an appointment without mentioning a speciality, ask them which speciality they need.
5. Call check_doctor_availability only after the patient specifies a speciality.
6. Show the available doctors and appointment slots.
7. Let the patient select a doctor and slot.
8. Ask for the patient's full name.
9. Ask for the patient's complete phone number.
10. Repeat every digit of the phone number individually.
11. Ask: "Is this phone number correct?"
12. Wait for an explicit YES.
13. Only after YES, call book_appointment.
14. When calling book_appointment, ALWAYS provide all four required arguments:
    - patient_name
    - phone_number
    - doctor_name
    - appointment_slot
15. Never omit patient_name or phone_number.
16. Use the exact doctor name and appointment slot selected by the patient.

CANCELLATION:
1. Ask which appointment the patient wants to cancel.
2. Collect the exact doctor's full name.
3. Collect the exact appointment date and time.
4. Convert the date and time into YYYY-MM-DD HH:MM AM/PM format.
5. Repeat the doctor name and appointment date/time.
6. Ask for explicit confirmation.
7. Only after an explicit YES, call cancel_appointment.
8. ALWAYS provide BOTH required arguments:
   - doctor_name
   - appointment_slot
9. Never call cancel_appointment with missing arguments.
10. Never invent or guess appointment details.
11. If the tool returns an error, explain it politely.

IMPORTANT RULES:
- Never book or cancel without the patient's explicit confirmation.
- Never assume a medical speciality. Ask the patient first.
- Available specialities are Cardiologist, Dermatologist, and Neurologist.
- Never invent doctors, slots, or appointment results.
- Never ask for OTP, login, or caller ID.
- Speak naturally and keep responses short.
- Ask one question at a time.
- If a tool returns an error, explain it politely.
"""



# TOOL 1: Check doctor availability
async def check_availability_handler(params: FunctionCallParams):
    result = availability_tool(
        params.arguments["speciality"]
    )
    await params.result_callback(result)


# TOOL 2: Book appointment
async def book_appointment_handler(params: FunctionCallParams):
    result = booking_tool(
        params.arguments["patient_name"],
        params.arguments["phone_number"],
        params.arguments["doctor_name"],
        params.arguments["appointment_slot"],
    )
    await params.result_callback(result)


# TOOL 3: Cancel appointment
async def cancel_appointment_handler(params: FunctionCallParams):
    result = cancellation_tool(
        params.arguments["doctor_name"],
        params.arguments["appointment_slot"],
    )
    await params.result_callback(result)


TOOLS = [
    FunctionSchema(
        name="check_doctor_availability",
        description="Check doctors and available slots for a medical speciality.",
        properties={
            "speciality": {
                "type": "string",
                "description": "Medical speciality, such as Cardiologist",
            }
        },
        required=["speciality"],
    ),
    FunctionSchema(
        name="book_appointment",
        description=(
            "Book an appointment. You MUST provide all four arguments: "
            "patient_name, phone_number, doctor_name, and appointment_slot. "
            "Never omit any argument. Only call after the patient confirms "
            "their phone number."
        ),
        properties={
            "patient_name": {
                "type": "string",
                "description": "Patient's full name",
            },
            "phone_number": {
                "type": "string",
                "description": "Phone number confirmed by the patient",
            },
            "doctor_name": {
                "type": "string",
                "description": "Selected doctor's full name",
            },
            "appointment_slot": {
                "type": "string",
                "description": "Selected appointment date and time",
            },
        },
        required=[
            "patient_name",
            "phone_number",
            "doctor_name",
            "appointment_slot",
        ],
    ),
    FunctionSchema(
        name="cancel_appointment",
        description=(
            "Cancel an existing appointment. You MUST provide both "
            "doctor_name and appointment_slot. Never omit either argument. "
            "Call only after explicit patient confirmation."
        ),
        properties={
            "doctor_name": {
                "type": "string",
                "description": "Doctor's full name",
            },
            "appointment_slot": {
                "type": "string",
                "description": "Appointment date and time",
            },
        },
        required=[
            "doctor_name",
            "appointment_slot",
        ],
    ),
]


async def run_bot(webrtc_connection):
    if not GROQ_API_KEY or not ELEVENLABS_API_KEY:
        raise ValueError("API keys missing. Check backend/.env")

    async with aiohttp.ClientSession() as session:

        transport = SmallWebRTCTransport(
            webrtc_connection=webrtc_connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
        )

        stt = ElevenLabsSTTService(
            api_key=ELEVENLABS_API_KEY,
            aiohttp_session=session,
        )

        llm = GroqLLMService(
            api_key=GROQ_API_KEY,
            model="openai/gpt-oss-20b",
            system_instruction=SYSTEM_PROMPT,
        )

        tts = ElevenLabsTTSService(
            api_key=ELEVENLABS_API_KEY,
            voice_id=ELEVENLABS_VOICE_ID,
        )

        # Register all three appointment tools with Gemini
        llm.register_function(
            "check_doctor_availability",
            check_availability_handler,
        )
        llm.register_function(
            "book_appointment",
            book_appointment_handler,
        )
        llm.register_function(
            "cancel_appointment",
            cancel_appointment_handler,
        )

        context = LLMContext(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ],
            tools=TOOLS,
        )

        user_aggregator, assistant_aggregator = (
            LLMContextAggregatorPair(
            context,
                user_params=LLMUserAggregatorParams(
                    vad_analyzer=SileroVADAnalyzer()
                ),
            )
        )

        pipeline = Pipeline(
            [
                transport.input(),
                stt,
                user_aggregator,
                llm,
                tts,
                transport.output(),
                assistant_aggregator,
            ]
        )

        worker = PipelineWorker(
            pipeline,
            params=PipelineParams(
                audio_in_sample_rate=16000,
                audio_out_sample_rate=24000,
            ),
        )

        runner = WorkerRunner(handle_sigint=False)

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            print("Patient connected.")
            await worker.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            print("Patient disconnected.")
            await runner.cancel()

        await runner.run(worker)
