from django.contrib import admin
from base.models import *

admin.site.register(CustomUser)
admin.site.register(Board)
admin.site.register(List)
admin.site.register(Card)
admin.site.register(Label)
admin.site.register(CardLabel)
admin.site.register(Checklist)
admin.site.register(ChecklistItem)
admin.site.register(Attachment)
admin.site.register(Comment)
admin.site.register(Activity)
