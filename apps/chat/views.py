from celery.result import AsyncResult
from celery_progress.backend import Progress
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.api_url_helpers import get_chat_api_url_templates
from apps.chat.models import Chat, ChatMessage
from apps.chat.serializers import ChatMessageSerializer, ChatSerializer
from apps.chat.tasks import get_chat_response, set_chat_name


@login_required
def chat_home(request):
    chats = request.user.chats.order_by("-updated_at")
    return TemplateResponse(
        request,
        "chat/chat_home.html",
        {
            "active_tab": "ai-chat",
            "chats": chats,
        },
    )


@require_POST
@login_required
def start_chat(request):
    chat = Chat.objects.create(
        user=request.user,
    )
    return HttpResponseRedirect(reverse("chat:single_chat", args=[chat.id]))


@login_required
def single_chat_react(request, chat_id: int):
    chat = get_object_or_404(Chat, user=request.user, id=chat_id)
    serialized_chat = ChatSerializer(chat).data
    return TemplateResponse(
        request,
        "chat/single_chat_react.html",
        {
            "active_tab": "ai-chat",
            "chat": chat,
            "serialized_chat": serialized_chat,
            "api_urls": get_chat_api_url_templates(),
        },
    )


@extend_schema(tags=["chat"], exclude=True)
class NewChatMessageAPI(mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(chat__user=self.request.user)

    @method_decorator(login_required)
    def post(self, request, chat_id, *args, **kwargs):
        # ensure user can access chat
        self.chat = get_object_or_404(Chat, user=self.request.user, id=chat_id)
        # set some values we'll need later
        self.chat_id = chat_id
        self.is_first_message = not self.chat.messages.exists()
        response = self.create(request, *args, **kwargs)
        response.data["task_id"] = self.task_id  # add task_id to the response so it can be queried
        return response

    def perform_create(self, serializer):
        if serializer.validated_data["chat"] != self.chat:
            raise ValidationError(_("Invalid Chat ID."))
        # save model
        instance = serializer.save()
        # process message
        result = get_chat_response.delay(self.chat_id, instance.content)
        self.task_id = result.task_id
        if self.is_first_message:
            set_chat_name.delay(self.chat_id, instance.content)


@extend_schema(tags=["chat"], exclude=True)
class GetMessageResponseAPI(APIView):
    serializer_class = ChatMessageSerializer

    def get(self, request, chat_id, task_id):
        get_object_or_404(Chat, user=self.request.user, id=chat_id)
        progress = Progress(AsyncResult(task_id))
        return Response(progress.get_info())
