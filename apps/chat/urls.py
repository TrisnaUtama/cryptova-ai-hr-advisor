from django.urls import path
from .views import ChatHistoryView, ChatRoomView

urlpatterns = [
    path("chat/history/", ChatHistoryView.as_view(), name="chat_history"),
    path("chat/", ChatRoomView.as_view(), name="chat"),
]
