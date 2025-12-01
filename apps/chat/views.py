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

from apps.chat.api_url_helpers import get_chat_api_url_templates, get_menu_urls
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
    serialized_chat = ChatSerializer(chat, context={'request': request}).data
    return TemplateResponse(
        request,
        "chat/single_chat_react.html",
        {
            "active_tab": "ai-chat",
            "chat": chat,
            "serialized_chat": serialized_chat,
            "api_urls": get_chat_api_url_templates(),
            "menu_urls": get_menu_urls(),
        },
    )


@login_required
def single_chat(request):
    """Get or create a single chat for the user - main chat interface"""
    # Get the most recent chat or create a new one
    chat = Chat.objects.filter(user=request.user).order_by('-updated_at').first()
    if not chat:
        chat = Chat.objects.create(user=request.user, name="Main Chat")
    
    serialized_chat = ChatSerializer(chat, context={'request': request}).data
    return TemplateResponse(
        request,
        "chat/single_chat_react.html",
        {
            "active_tab": "ai-chat",
            "chat": chat,
            "serialized_chat": serialized_chat,
            "api_urls": get_chat_api_url_templates(),
            "menu_urls": get_menu_urls(),
        },
    )


@extend_schema(tags=["chat"], exclude=True)
class NewChatMessageAPI(mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(chat__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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
        if serializer.validated_data.get("chat") and serializer.validated_data["chat"] != self.chat:
            raise ValidationError(_("Invalid Chat ID."))
        # Set chat if not provided
        if "chat" not in serializer.validated_data:
            serializer.validated_data["chat"] = self.chat
        
        # Handle file upload
        attachment = self.request.FILES.get('attachment')
        if attachment:
            # Determine attachment type from file extension
            file_name = attachment.name.lower()
            if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                attachment_type = 'image'
            elif file_name.endswith('.csv'):
                attachment_type = 'csv'
            elif file_name.endswith('.pdf'):
                attachment_type = 'pdf'
            else:
                attachment_type = 'other'
            serializer.validated_data['attachment'] = attachment
            serializer.validated_data['attachment_type'] = attachment_type
        
        # save model
        instance = serializer.save()
        # process message
        result = get_chat_response.delay(self.chat_id, instance.id)
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


@extend_schema(tags=["chat"], exclude=True)
class ClearChatHistoryAPI(APIView):
    @method_decorator(login_required)
    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, user=request.user, id=chat_id)
        # Delete all messages in the chat
        chat.messages.all().delete()
        return Response({"status": "success", "message": "Chat history cleared"})


@extend_schema(tags=["chat"], exclude=True)
class UserDataAPI(APIView):
    """API endpoint to get user's personal details and Plaid account data"""
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        data = {
            "user": {
                "name": user.get_full_name() or user.username,
                "email": user.email,
            },
            "linked_accounts": [],
            "recent_transactions": [],
            "investment_holdings": [],
        }
        
        try:
            from apps.records.models import LinkedAccount, AccountBalance, FinancialTransaction, InvestmentHolding
            
            # Get linked accounts
            linked_accounts = LinkedAccount.objects.filter(user=user, status='active')
            for account in linked_accounts:
                latest_balance = AccountBalance.objects.filter(account=account).order_by('-balance_date').first()
                account_data = {
                    "id": account.id,
                    "institution_name": account.institution_name,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "balance": str(latest_balance.current_balance) if latest_balance else "0.00",
                }
                data["linked_accounts"].append(account_data)
            
            # Get recent transactions
            recent_transactions = FinancialTransaction.objects.filter(
                account__user=user
            ).order_by('-date')[:20]
            for transaction in recent_transactions:
                data["recent_transactions"].append({
                    "id": transaction.id,
                    "date": str(transaction.date),
                    "amount": str(transaction.amount),
                    "description": transaction.description,
                    "category": transaction.category,
                    "account_name": transaction.account.account_name,
                })
            
            # Get investment holdings
            holdings = InvestmentHolding.objects.filter(account__user=user).order_by('-as_of_date')[:20]
            for holding in holdings:
                data["investment_holdings"].append({
                    "id": holding.id,
                    "security_name": holding.security_name,
                    "security_ticker": holding.security_ticker,
                    "quantity": str(holding.quantity),
                    "value": str(holding.value),
                    "account_name": holding.account.account_name,
                })
        except ImportError:
            pass
        
        return Response(data)
