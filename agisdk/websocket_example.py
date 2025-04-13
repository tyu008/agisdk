import json
import requests
import websocket

# Step 1. Retrieve the list of available targets from Chrome.
debug_url = "http://localhost:52108/json"
response = requests.get(debug_url)
targets = response.json()

# Pick a target that contains a WebSocket debugger URL.
target = None
for t in targets:
    if "webSocketDebuggerUrl" in t:
        target = t
        break

if target is None:
    raise Exception("No target with a WebSocket debugger URL was found.")

ws_url = target["webSocketDebuggerUrl"]
print("Connecting to target at:", ws_url)

# Step 2. Connect to the target using a synchronous WebSocket client.
ws = websocket.create_connection(ws_url)

# (Optional) If you want to use other methods, you might first enable the Page domain:
enable_page_cmd = {
    "id": 1,
    "method": "Page.enable"
}
ws.send(json.dumps(enable_page_cmd))
print("Sent Page.enable command.")
print("Response:", ws.recv())

# Step 3. Send a CDP command to navigate to Gmail.
navigate_cmd = {
    "id": 2,  # use an incremental id; you must ensure id uniqueness for your session.
    "method": "Page.navigate",
    "params": {
        "url": "https://www.gmail.com"
    }
}
ws.send(json.dumps(navigate_cmd))
print("Sent Page.navigate command to load Gmail.")

# Wait for the response from the browser (this returns a JSON string).
response = ws.recv()
print("Navigate response:", response)

# Step 4. Disconnect from the WebSocket.
# This leaves the browser window open, only disconnecting the CDP session.
ws.close()
print("Disconnected from the CDP session.")