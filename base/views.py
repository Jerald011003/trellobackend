from django.contrib.auth.models import User
from base.models import (
    CustomUser, Board, List, Card, Label, CardLabel, 
    Checklist, ChecklistItem, Attachment, Comment, Activity
)
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from django.contrib.auth.hashers import make_password
from .serializer import (
    UserSerializer, UserSerializerWithToken, BoardSerializer, 
    BoardDetailSerializer, ListSerializer, CardSerializer,
    LabelSerializer, ChecklistSerializer, ChecklistItemSerializer,
    AttachmentSerializer, CommentSerializer, ActivitySerializer
)
from datetime import datetime
from rest_framework.views import APIView
from django.db.models import Q

@api_view(['GET'])
def getRoutes(request):
    routes = [
        '/api/users/register/',
        '/api/users/login/',
        '/api/users/profile/',
        '/api/boards/',
        '/api/boards/<id>/',
        '/api/lists/',
        '/api/cards/',
    ]
    return Response(routes)

# !! Auth
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerWithToken(self.user).data
        for k, v in serializer.items():
            data[k] = v
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# !! Users
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

@api_view(['GET'])
# @permission_classes([IsAdminUser])
def getUsers(request):
    users = CustomUser.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
# @permission_classes([IsAdminUser])
def getUserById(request, pk):
    user = CustomUser.objects.get(id=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def registerUser(request):
    data = request.data
    
    if CustomUser.objects.filter(email=data['email']).exists():
        message = {'details': 'User with this email already exists'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.create(
            first_name=data['name'],
            email=data['email'],
            password=make_password(data['password'])
        )
        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        message = {'details': 'An error occurred while creating the user'}
        return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUserProfile(request):
    user = request.user
    serializer = UserSerializerWithToken(user, many=False)

    data = request.data
    user.first_name = data['name']
    user.email = data['email']

    if data['password'] != '':
        user.password = make_password(data['password'])

    user.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateUser(request, pk):
    user = CustomUser.objects.get(id=pk)

    data = request.data

    user.first_name = data['name']
    user.email = data['email']
    user.is_staff = data['isAdmin']

    user.save()

    serializer = UserSerializer(user, many=False)

    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteUser(request, pk):
    userForDeletion = CustomUser.objects.get(id=pk)
    userForDeletion.delete()
    return Response('User was deleted')

# !! Boards
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getBoards(request):
    # Get boards where user is owner or member
    user = request.user
    owned_boards = Board.objects.filter(owner=user, is_archived=False)
    member_boards = user.member_boards.filter(is_archived=False)
    
    # Combine querysets
    boards = owned_boards | member_boards
    
    serializer = BoardSerializer(boards, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createBoard(request):
    user = request.user
    data = request.data
    
    board = Board.objects.create(
        owner=user,
        title=data['title'],
        description=data.get('description', ''),
        background_color=data.get('background_color', '')
    )
    
    # Create default lists
    List.objects.create(title='To Do', board=board, position=1)
    List.objects.create(title='In Progress', board=board, position=2)
    List.objects.create(title='Done', board=board, position=3)
    
    # Create activity
    Activity.objects.create(
        user=user,
        action='create_board',
        board=board
    )
    
    serializer = BoardSerializer(board, many=False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getBoardDetail(request, pk):
    try:
        board = Board.objects.get(pk=pk)
        
        # Check if user has access to this board
        user = request.user
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to view this board'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        serializer = BoardDetailSerializer(board, many=False)
        return Response(serializer.data)
    except Board.DoesNotExist:
        return Response({'detail': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateBoard(request, pk):
    try:
        board = Board.objects.get(pk=pk)
        
        # Check if user is the owner
        user = request.user
        if board.owner != user:
            return Response({'detail': 'Only the board owner can update it'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        board.title = data.get('title', board.title)
        board.description = data.get('description', board.description)
        board.background_color = data.get('background_color', board.background_color)
        board.save()
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='update_board',
            board=board
        )
        
        serializer = BoardSerializer(board, many=False)
        return Response(serializer.data)
    except Board.DoesNotExist:
        return Response({'detail': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteBoard(request, pk):
    try:
        board = Board.objects.get(pk=pk)
        
        # Check if user is the owner
        user = request.user
        if board.owner != user:
            return Response({'detail': 'Only the board owner can delete it'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        board.delete()
        return Response({'detail': 'Board deleted successfully'})
    except Board.DoesNotExist:
        return Response({'detail': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addBoardMember(request, pk):
    try:
        board = Board.objects.get(pk=pk)
        
        # Check if user is the owner
        user = request.user
        if board.owner != user:
            return Response({'detail': 'Only the board owner can add members'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        email = data.get('email')
        
        try:
            member = CustomUser.objects.get(email=email)
            board.members.add(member)
            
            # Create activity
            Activity.objects.create(
                user=user,
                action='add_member',
                board=board,
                data={'member_id': member.id, 'member_name': member.get_full_name()}
            )
            
            return Response({'detail': f'{member.get_full_name()} added to board'})
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Board.DoesNotExist:
        return Response({'detail': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

# !! Lists
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createList(request):
    user = request.user
    data = request.data
    
    try:
        board = Board.objects.get(pk=data['board_id'])
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to add lists to this board'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        # Get the highest position and add 1
        highest_position = List.objects.filter(board=board).order_by('-position').first()
        position = 1
        if highest_position:
            position = highest_position.position + 1
        
        list_obj = List.objects.create(
            title=data['title'],
            board=board,
            position=position
        )
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='create_list',
            board=board,
            list=list_obj
        )
        
        serializer = ListSerializer(list_obj, many=False)
        return Response(serializer.data)
    except Board.DoesNotExist:
        return Response({'detail': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateList(request, pk):
    user = request.user
    data = request.data
    
    try:
        list_obj = List.objects.get(pk=pk)
        board = list_obj.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to update lists on this board'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        list_obj.title = data.get('title', list_obj.title)
        list_obj.position = data.get('position', list_obj.position)
        list_obj.save()
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='update_list',
            board=board,
            list=list_obj
        )
        
        serializer = ListSerializer(list_obj, many=False)
        return Response(serializer.data)
    except List.DoesNotExist:
        return Response({'detail': 'List not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteList(request, pk):
    user = request.user
    
    try:
        list_obj = List.objects.get(pk=pk)
        board = list_obj.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to delete lists on this board'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        list_obj.delete()
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='archive_list',
            board=board,
            data={'list_title': list_obj.title}
        )
        
        return Response({'detail': 'List deleted successfully'})
    except List.DoesNotExist:
        return Response({'detail': 'List not found'}, status=status.HTTP_404_NOT_FOUND)

# !! Cards
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createCard(request):
    user = request.user
    data = request.data
    
    try:
        list_obj = List.objects.get(pk=data['list_id'])
        board = list_obj.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to add cards to this board'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        # Get the highest position and add 1
        highest_position = Card.objects.filter(list=list_obj).order_by('-position').first()
        position = 1
        if highest_position:
            position = highest_position.position + 1
        
        card = Card.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            list=list_obj,
            position=position,
            created_by=user
        )
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='create_card',
            board=board,
            list=list_obj,
            card=card
        )
        
        serializer = CardSerializer(card, many=False)
        return Response(serializer.data)
    except List.DoesNotExist:
        return Response({'detail': 'List not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getCardDetail(request, pk):
    user = request.user
    
    try:
        card = Card.objects.get(pk=pk)
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to view this card'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        serializer = CardSerializer(card, many=False)
        return Response(serializer.data)
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateCard(request, pk):
    user = request.user
    data = request.data
    
    try:
        card = Card.objects.get(pk=pk)
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to update this card'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        card.title = data.get('title', card.title)
        card.description = data.get('description', card.description)
        card.due_date = data.get('due_date', card.due_date)
        card.position = data.get('position', card.position)
        
        # If list_id is provided, move the card to that list
        if 'list_id' in data and int(data['list_id']) != card.list.id:
            try:
                new_list = List.objects.get(pk=data['list_id'])
                
                # Check if the new list belongs to the same board
                if new_list.board.id != board.id:
                    return Response({'detail': 'Cannot move card to a list on a different board'}, 
                                    status=status.HTTP_400_BAD_REQUEST)
                
                old_list = card.list
                card.list = new_list
                
                # Create move activity
                Activity.objects.create(
                    user=user,
                    action='move_card',
                    board=board,
                    list=new_list,
                    card=card,
                    data={'from_list': old_list.title, 'to_list': new_list.title}
                )
            except List.DoesNotExist:
                return Response({'detail': 'List not found'}, status=status.HTTP_404_NOT_FOUND)
        
        card.save()
        
        # Create update activity
        Activity.objects.create(
            user=user,
            action='update_card',
            board=board,
            list=card.list,
            card=card
        )
        
        serializer = CardSerializer(card, many=False)
        return Response(serializer.data)
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteCard(request, pk):
    user = request.user
    
    try:
        card = Card.objects.get(pk=pk)
        board = card.list.board
        list_obj = card.list
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to delete this card'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        card.delete()
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='archive_card',
            board=board,
            list=list_obj,
            data={'card_title': card.title}
        )
        
        return Response({'detail': 'Card deleted successfully'})
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)

# !! Comments
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addComment(request, pk):
    user = request.user
    data = request.data
    
    try:
        card = Card.objects.get(pk=pk)
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to comment on this card'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        comment = Comment.objects.create(
            text=data['text'],
            card=card,
            author=user
        )
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='add_comment',
            board=board,
            list=card.list,
            card=card
        )
        
        serializer = CommentSerializer(comment, many=False)
        return Response(serializer.data)
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)

# !! Attachments
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addAttachment(request, pk):
    user = request.user
    
    try:
        card = Card.objects.get(pk=pk)
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to add attachments to this card'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        attachment = Attachment.objects.create(
            file=file,
            name=file.name,
            card=card,
            uploaded_by=user
        )
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='add_attachment',
            board=board,
            list=card.list,
            card=card
        )
        
        serializer = AttachmentSerializer(attachment, many=False)
        return Response(serializer.data)
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)

# !! Checklists
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createChecklist(request, pk):
    user = request.user
    data = request.data
    
    try:
        card = Card.objects.get(pk=pk)
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to add checklists to this card'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        checklist = Checklist.objects.create(
            title=data['title'],
            card=card
        )
        
        # Create activity
        Activity.objects.create(
            user=user,
            action='add_checklist',
            board=board,
            list=card.list,
            card=card
        )
        
        serializer = ChecklistSerializer(checklist, many=False)
        return Response(serializer.data)
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addChecklistItem(request, pk):
    user = request.user
    data = request.data
    
    try:
        checklist = Checklist.objects.get(pk=pk)
        card = checklist.card
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to add items to this checklist'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        item = ChecklistItem.objects.create(
            text=data['text'],
            checklist=checklist
        )
        
        serializer = ChecklistItemSerializer(item, many=False)
        return Response(serializer.data)
    except Checklist.DoesNotExist:
        return Response({'detail': 'Checklist not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def toggleChecklistItem(request, pk):
    user = request.user
    
    try:
        item = ChecklistItem.objects.get(pk=pk)
        checklist = item.checklist
        card = checklist.card
        board = card.list.board
        
        # Check if user has access to this board
        if board.owner != user and user not in board.members.all():
            return Response({'detail': 'You do not have permission to update this checklist item'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        item.is_completed = not item.is_completed
        item.save()
        
        if item.is_completed:
            # Create activity
            Activity.objects.create(
                user=user,
                action='complete_checklist_item',
                board=board,
                list=card.list,
                card=card
            )
        
        serializer = ChecklistItemSerializer(item, many=False)
        return Response(serializer.data)
    except ChecklistItem.DoesNotExist:
        return Response({'detail': 'Checklist item not found'}, status=status.HTTP_404_NOT_FOUND)

# !! Search
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_api(request):
    query = request.GET.get('q', '')
    user = request.user
    
    # Get boards where user is owner or member
    owned_boards = Board.objects.filter(owner=user)
    member_boards = user.member_boards.all()
    accessible_boards = (owned_boards | member_boards).distinct()
    
    # Search boards
    board_results = accessible_boards.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    )
    
    # Get all lists from accessible boards
    accessible_lists = List.objects.filter(board__in=accessible_boards)
    
    # Search lists
    list_results = accessible_lists.filter(title__icontains=query)
    
    # Get all cards from accessible lists
    accessible_cards = Card.objects.filter(list__in=accessible_lists)
    
    # Search cards
    card_results = accessible_cards.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    )
    
    # Serialize the data
    board_data = BoardSerializer(board_results, many=True).data
    list_data = ListSerializer(list_results, many=True).data
    card_data = CardSerializer(card_results, many=True).data
    
    return Response({
        'query': query,
        'board_results': board_data,
        'list_results': list_data,
        'card_results': card_data,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_boards(request):
    query = request.GET.get('q', '')
    if not query:
        return Response([])
        
    user = request.user
    
    # Get boards where user is owner or member
    owned_boards = Board.objects.filter(owner=user)
    member_boards = Board.objects.filter(members=user)
    accessible_boards = (owned_boards | member_boards).distinct()
    
    # Search boards
    results = accessible_boards.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query)
    )
    
    serializer = BoardSerializer(results, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_cards(request):
    query = request.GET.get('q', '')
    if not query:
        return Response([])
        
    user = request.user
    
    # Get boards where user is owner or member
    owned_boards = Board.objects.filter(owner=user)
    member_boards = Board.objects.filter(members=user)
    accessible_boards = (owned_boards | member_boards).distinct()
    
    # Get all lists from accessible boards
    board_ids = [board.id for board in accessible_boards]
    accessible_lists = List.objects.filter(board_id__in=board_ids)
    
    # Get all cards from accessible lists
    list_ids = [list_.id for list_ in accessible_lists]
    accessible_cards = Card.objects.filter(list_id__in=list_ids)
    
    # Search cards
    results = accessible_cards.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query)
    )
    
    serializer = CardSerializer(results, many=True)
    return Response(serializer.data)

# !List Reordering
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reorderLists(request, pk):
    try:
        board = Board.objects.get(id=pk)
        list_ids = request.data.get('list_ids', [])
        
        if not list_ids:
            return Response({'detail': 'List IDs are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update the order of lists - use position field instead of order
        for index, list_id in enumerate(list_ids):
            try:
                list_obj = List.objects.get(id=list_id, board=board)
                list_obj.position = index  # Change order to position
                list_obj.save()
            except List.DoesNotExist:
                pass
                
        return Response({'detail': 'Lists reordered successfully'}, status=status.HTTP_200_OK)
            
    except Board.DoesNotExist:
        return Response({'detail': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reorderCards(request, pk):
    try:
        list_obj = List.objects.get(id=pk)
        card_ids = request.data.get('card_ids', [])
        
        if not card_ids:
            return Response({'detail': 'Card IDs are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update the order of cards
        for index, card_id in enumerate(card_ids):
            try:
                card = Card.objects.get(id=card_id, list=list_obj)
                card.order = index
                card.save()
            except Card.DoesNotExist:
                pass
                
        return Response({'detail': 'Cards reordered successfully'}, status=status.HTTP_200_OK)
            
    except List.DoesNotExist:
        return Response({'detail': 'List not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def moveCard(request, pk):
    try:
        card = Card.objects.get(id=pk)
        source_list_id = request.data.get('source_list_id')
        destination_list_id = request.data.get('destination_list_id')
        new_order = request.data.get('new_order', [])
        
        if not destination_list_id:
            return Response({'detail': 'Destination list ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update the card's list
        try:
            destination_list = List.objects.get(id=destination_list_id)
            card.list = destination_list
            card.save()
            
            # Update order of cards in the destination list
            for index, card_id in enumerate(new_order):
                try:
                    c = Card.objects.get(id=card_id, list=destination_list)
                    c.order = index
                    c.save()
                except Card.DoesNotExist:
                    pass
                    
            return Response({'detail': 'Card moved successfully'}, status=status.HTTP_200_OK)
                
        except List.DoesNotExist:
            return Response({'detail': 'Destination list not found'}, status=status.HTTP_404_NOT_FOUND)
            
    except Card.DoesNotExist:
        return Response({'detail': 'Card not found'}, status=status.HTTP_404_NOT_FOUND)
    
