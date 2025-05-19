from django.urls import path

from .views import ChatHistoryView, ChatRoomView, create_chat_session

urlpatterns = [
    path("chat/history/", ChatHistoryView.as_view(), name="chat_history"),
    path("chat/", ChatRoomView.as_view(), name="chat"),
    path("chat/create-session/", create_chat_session, name="create_chat_session"),
]
