from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="chat_home"),
    path("chat/start/", views.start_chat, name="start_chat"),
    path("chat/<int:chat_id>/", views.single_chat_react, name="single_chat"),
    path("chat/<int:chat_id>/new_message/", views.NewChatMessageAPI.as_view(), name="api_new_chat_message"),
    path(
        "chat/<int:chat_id>/get_response/<slug:task_id>/",
        views.GetMessageResponseAPI.as_view(),
        name="api_get_message_response",
    ),
]
