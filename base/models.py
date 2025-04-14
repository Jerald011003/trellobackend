from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Board(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_boards')
    members = models.ManyToManyField(CustomUser, related_name='member_boards', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    background_color = models.CharField(max_length=50, default="blue-600")
    background_image = models.ImageField(upload_to='board_backgrounds/', blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class List(models.Model):
    title = models.CharField(max_length=255)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.title

class Card(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='cards')
    position = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_cards')
    assigned_to = models.ManyToManyField(CustomUser, related_name='assigned_cards', blank=True)
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='card_covers/', blank=True, null=True)
    cover_color = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.title

class Label(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='labels')
    
    def __str__(self):
        return self.name

class CardLabel(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='card_labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='label_cards')
    
    class Meta:
        unique_together = ('card', 'label')

class Checklist(models.Model):
    title = models.CharField(max_length=255)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='checklists')
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return self.title

class ChecklistItem(models.Model):
    text = models.CharField(max_length=255)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
    is_completed = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return self.text

class Attachment(models.Model):
    file = models.FileField(upload_to='card_attachments/')
    name = models.CharField(max_length=255)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Comment(models.Model):
    text = models.TextField()
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.card}"

class Activity(models.Model):
    ACTION_CHOICES = (
        ('create_board', 'Created board'),
        ('update_board', 'Updated board'),
        ('archive_board', 'Archived board'),
        ('create_list', 'Created list'),
        ('update_list', 'Updated list'),
        ('archive_list', 'Archived list'),
        ('create_card', 'Created card'),
        ('update_card', 'Updated card'),
        ('move_card', 'Moved card'),
        ('archive_card', 'Archived card'),
        ('add_member', 'Added member'),
        ('remove_member', 'Removed member'),
        ('add_comment', 'Added comment'),
        ('add_attachment', 'Added attachment'),
        ('remove_attachment', 'Removed attachment'),
        ('add_checklist', 'Added checklist'),
        ('complete_checklist_item', 'Completed checklist item'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    list = models.ForeignKey(List, on_delete=models.CASCADE, null=True, blank=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)  # For storing additional context
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.user} {self.get_action_display()} on {self.board}"
