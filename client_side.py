import asyncio
import cv2
from aiortc import RTCPeerConnection, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling

# Flag to control the streaming
streaming_active = True

async def run_client():
    global streaming_active

    signaling = TcpSocketSignaling("127.0.0.1", 12345)
    pc = RTCPeerConnection()

    # Handle video track
    @pc.on("track")
    async def on_track(track):
        print("Receiving video stream...")
        if isinstance(track, VideoStreamTrack):
            while streaming_active:
                frame = await track.recv()
                img = frame.to_ndarray(format="bgr24")
                cv2.imshow("Remote Stream", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to stop streaming
                    streaming_active = False
                    break
            cv2.destroyAllWindows()

    try:
        # Connect to server
        await signaling.connect()
        local_description = await signaling.receive()
        await pc.setRemoteDescription(local_description)
        await pc.setLocalDescription(await pc.createAnswer())
        await signaling.send(pc.localDescription)

        # Keep
