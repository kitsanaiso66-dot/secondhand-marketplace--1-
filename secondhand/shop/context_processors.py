from .models import Message


def unread_chats(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    n = (
        Message.objects.filter(is_read=False)
        .exclude(sender=user)
        .filter(conversation__buyer=user)
        .count()
        + Message.objects.filter(is_read=False, conversation__product__seller=user)
        .exclude(sender=user)
        .count()
    )
    return {"unread_chat_count": n}