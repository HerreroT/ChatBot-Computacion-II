from __future__ import annotations

def test_websocket_receives_booking_event(sync_client):
    with sync_client.websocket_connect("/ws/admin") as websocket:
        handshake = websocket.receive_json()
        assert handshake["event"] == "connected"

        resp = sync_client.post(
            "/webhook/whatsapp",
            json={"from": "+549261333333", "text": "corte 25/08 16:00"},
        )
        assert resp.status_code == 200

        event = websocket.receive_json()
        assert event["event"] == "booking.created"
        assert event["data"]["user"] == "+549261333333"
