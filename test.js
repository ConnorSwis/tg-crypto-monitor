const wsUrl = "ws://localhost:3000/latest"; // Replace with your WebSocket URL
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log("Connected to WebSocket server");
};

ws.onmessage = (event) => {
  console.log("Message received:", event.data);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = (event) => {
  console.log(`WebSocket closed. Code: ${event.code}, Reason: ${event.reason}`);
};
