
import { useEffect, useRef, useState } from "react";
import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import "./App.css";

function App() {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [callStatus, setCallStatus] = useState("Disconnected");
  const [transcript, setTranscript] = useState([]);
  const [error, setError] = useState("");

  const clientRef = useRef(null);
  const audioRef = useRef(null);

  const API_URL = "http://localhost:8000";

  async function loadData() {
    try {
      const [doctorResponse, appointmentResponse] = await Promise.all([
        fetch(`${API_URL}/api/doctors`),
        fetch(`${API_URL}/api/appointments`),
      ]);

      const doctorData = await doctorResponse.json();
      const appointmentData = await appointmentResponse.json();

      setDoctors(doctorData.doctors);
      setAppointments(appointmentData.appointments);
    } catch (error) {
      console.error("Could not load data:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function startCall() {
    try {
      setError("");
      setTranscript([]);
      setCallStatus("Connecting...");

      const client = new PipecatClient({
        transport: new SmallWebRTCTransport(),
        enableMic: true,
        enableCam: false,
        callbacks: {
          onConnected: () => {
            setCallStatus("Connected");
          },

          onDisconnected: () => {
            setCallStatus("Disconnected");
            loadData();
          },

          onBotReady: () => {
            setCallStatus("Connected");
          },

          onTrackStarted: (track, participant) => {
            if (participant?.local || track.kind !== "audio") return;

            if (audioRef.current) {
              audioRef.current.srcObject = new MediaStream([track]);

              audioRef.current.play().catch((err) => {
              console.error("Audio playback error:", err);
              });
            }
          },

          onUserInput: (data) => {
            setTranscript((previous) => [
              ...previous,
              { speaker: "You", text: data.text },
            ]);
          },

          onBotOutput: (data) => {
  if (
    data.text &&
    data.aggregated_by === "sentence" &&
    data.spoken_status === "completed"
  ) {
    setTranscript((previous) => {
      const alreadyExists = previous.some(
        (message) =>
          message.speaker === "Doctor AI" &&
          message.segmentId === data.segment_id
      );

      if (alreadyExists) return previous;

      return [
        ...previous,
        {
          speaker: "Doctor AI",
          text: data.text,
          segmentId: data.segment_id,
        },
      ];
    });
  }
},

      
          onError: (message) => {
            setError(message?.data?.error || "Voice connection error");
          },
        },
      });

      clientRef.current = client;

      await client.connect({
        connection_url: `${API_URL}/api/offer`,
      });
    } catch (err) {
      console.error("Call error:", err);
      setCallStatus("Disconnected");
      setError(err.message || "Could not start the call.");
    }
  }

  async function endCall() {
    try {
      if (clientRef.current) {
        await clientRef.current.disconnect();
        clientRef.current = null;
      }

      setCallStatus("Disconnected");
      loadData();
    } catch (err) {
      console.error("Disconnect error:", err);
      setError(err.message);
    }
  }

  if (loading) {
    return <h3 className="text-center mt-5">Loading...</h3>;
  }

  return (
    <div className="container py-4">
      <audio ref={audioRef} autoPlay playsInline />
      <header className="text-center mb-5">
        <h1>NexovAI</h1>
        <p className="text-muted">
          Voice AI Doctor Appointment Assistant
        </p>
      </header>

      <section className="call-card text-center mb-5 p-4">
        <h2>Talk to Your AI Doctor Assistant</h2>

        <p className="text-muted">
          Book or cancel appointments using your voice.
        </p>

        <div className="my-4">
          <div className="call-icon">🎙️</div>
          <h5 className="mt-3">{callStatus}</h5>
        </div>

        <button
          className="btn btn-success btn-lg me-2"
          onClick={startCall}
          disabled={callStatus !== "Disconnected"}
        >
          Start Call
        </button>

        <button
          className="btn btn-danger btn-lg"
          onClick={endCall}
          disabled={callStatus === "Disconnected"}
        >
          End Call
        </button>

        {error && (
          <p className="text-danger mt-3">{String(error)}</p>
        )}
      </section>

      <section className="mb-5">
        <h2 className="mb-3">Live Conversation</h2>

        <div className="transcript-box p-3">
          {transcript.length === 0 ? (
            <p className="text-muted mb-0">
              Your conversation will appear here.
            </p>
          ) : (
            transcript.map((item, index) => (
              <p key={index}>
                <strong>{item.speaker}:</strong> {item.text}
              </p>
            ))
          )}
        </div>
      </section>

      <section className="mb-4">
        <h2 className="mb-3">Available Doctors</h2>

        <div className="row">
          {doctors.map((doctor) => (
            <div className="col-md-4 mb-3" key={doctor.id}>
              <div className="card p-3 h-100">
                <h5>{doctor.name}</h5>
                <p>{doctor.speciality}</p>
                <strong>Available Slots</strong>

                {doctor.available_slots.map((slot) => (
                  <p className="mb-1" key={slot}>{slot}</p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <hr className="my-4" />

      <section>
        <h2 className="mb-3">Appointments</h2>

        {appointments.length === 0 ? (
          <p>No appointments booked yet.</p>
        ) : (
          appointments.map((appointment, index) => (
            <div className="card p-3 mb-2" key={index}>
              <h5>{appointment.patient_name}</h5>
              <p className="mb-1">
              <strong>Patient Phone:</strong> {appointment.phone_number || "Not available"}
              </p>
              <p className="mb-1">
              <strong>Doctor:</strong> {appointment.doctor_name}
              </p>
              <p className="mb-1">
              <strong>Speciality:</strong> {appointment.speciality}
              </p>
              <p className="mb-1">
              <strong>Appointment:</strong> {appointment.appointment_slot}
              </p>
            </div>
          ))
        )}
      </section>
    </div>
  );
}

export default App;
