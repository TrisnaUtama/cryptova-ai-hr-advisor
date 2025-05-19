from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_notification(notification_type, content, document_id):
    """
    Sends a notification message to the WebSocket group "notifications".

    Args:
        notification_type (str): The type of notification.
        content (str): The content of the notification.
    """
    channel = get_channel_layer()
    if channel is None:
        print("Channel layer is None")
        return
        
    async_to_sync(channel.group_send)(
        "notifications",
        {
            "type": "send_notification",
            "message": {
                "content": content,
                "type": notification_type,
                "document_id": document_id,
            },
        },
    )


def send_chat_message(session_id, message):
    if not session_id:
        print("Session ID is None")
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Channel layer is None")
        return

    group_name = f"chat_{session_id}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_message",
            "message": message,
        },
    )
