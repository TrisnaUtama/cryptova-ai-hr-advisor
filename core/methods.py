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
