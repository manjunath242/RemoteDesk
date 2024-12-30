import asyncio
import cv2
import pygetwindow as gw
import pyautogui
from av import VideoFrame
from aiortc import RTCPeerConnection, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling

# Flag to control streaming
streaming_active = True

# Custom Video Track to Stream Window Content
class WindowCaptureTrack(VideoStreamTrack):
    def __init__(self, window_title):
        super().__init__()
        self.window_title = window_title

    async def recv(self):
        global streaming_active
        if not streaming_active:
            return None

        # Capture window screenshot
        windows = gw.getWindowsWithTitle(self.window_title)
        if not windows:
            raise ValueError(f"No window found with title: {self.window_title}")
        window = windows[0]
        bbox = (window.left, window.top, window.right, window.bottom)
        screenshot = pyautogui.screenshot(region=bbox)
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Convert to VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = self._next_pts
        video_frame.time_base = self.time_base
        return video_frame

async def run_server(window_title):
    global streaming_active

    # Initialize signaling and peer connection
    signaling = TcpSocketSignaling("127.0.0.1", 12345)
    pc = RTCPeerConnection()

    # Add video track
    video_track = WindowCaptureTrack(window_title)
    pc.addTrack(video_track)

    # Handle signaling
    await signaling.connect()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    @pc.on("connectionstatechange")
    def on_connectionstatechange():
        print(f"Connection state: {pc.connectionState}")
        if pc.connectionState == "failed":
            asyncio.run(pc.close())

    try:
        # Wait for client response
        remote_description = await signaling.receive()
        await pc.setRemoteDescription(remote_description)

        # Main loop for streaming
        while streaming_active:
            await asyncio.sleep(1)  # Check streaming state periodically

    except Exception as e:
        print(f"Error: {e}")

    finally:
        print("Stopping server...")
        streaming_active = False
        await pc.close()
        await signaling.close()

if __name__ == "__main__":
    window_title = input("Enter the title of the window to stream: ")
    try:
        asyncio.run(run_server(window_title))
    except KeyboardInterrupt:
        streaming_active = False
        print("Server stopped.")
