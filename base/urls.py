from django.urls import path
from base import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', views.getRoutes, name="getRoutes"),
    
    # !! Users
    path('users/register/', views.registerUser, name='register'),
    path('users/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', views.getUserProfile, name="getUserProfiles"),
    path('users/', views.getUsers, name="getUsers"),
    path('users/profile/update/', views.updateUserProfile, name="user-profile-update"),
    path('users/<str:pk>/', views.getUserById, name='user'),
    path('users/update/<str:pk>/', views.updateUser, name='user-update'),
    path('users/delete/<str:pk>/', views.deleteUser, name='user-delete'),
    
    # !! Boards
    path('boards/', views.getBoards, name='get-boards'),
    path('boards/create/', views.createBoard, name='create-board'),
    path('boards/<int:pk>/', views.getBoardDetail, name='get-board-detail'),
    path('boards/<str:pk>/update/', views.updateBoard, name='update-board'),
    path('boards/<str:pk>/delete/', views.deleteBoard, name='delete-board'),
    path('boards/<str:pk>/members/add/', views.addBoardMember, name='add-board-member'),
    
    # !! Lists
    path('lists/create/', views.createList, name='create-list'),
    path('lists/<str:pk>/update/', views.updateList, name='update-list'),
    path('lists/<str:pk>/delete/', views.deleteList, name='delete-list'),
    
    # !! Cards
    path('cards/create/', views.createCard, name='create-card'),
    path('cards/<int:pk>/', views.getCardDetail, name='get-card-detail'),
    path('cards/<str:pk>/update/', views.updateCard, name='update-card'),
    path('cards/<str:pk>/delete/', views.deleteCard, name='delete-card'),
    path('cards/<str:pk>/comments/add/', views.addComment, name='add-comment'),
    path('cards/<str:pk>/attachments/add/', views.addAttachment, name='add-attachment'),
    path('cards/<str:pk>/checklists/create/', views.createChecklist, name='create-checklist'),
    
    # !! Checklists
    path('checklists/<str:pk>/items/add/', views.addChecklistItem, name='add-checklist-item'),
    path('checklist-items/<str:pk>/toggle/', views.toggleChecklistItem, name='toggle-checklist-item'),
    
    # !! Search
    path('boards/search/', views.search_boards, name='search-boards'),
    path('cards/search/', views.search_cards, name='search-cards'),
    path('search/', views.search_api, name='search-api'),
    
     # Board reordering
    path('boards/<str:pk>/reorder-lists/', views.reorderLists, name='reorder-lists'),
    
    # List reordering
    path('lists/<str:pk>/reorder-cards/', views.reorderCards, name='reorder-cards'),
    
    # Card moving
    path('cards/<str:pk>/move/', views.moveCard, name='move-card'),
]
