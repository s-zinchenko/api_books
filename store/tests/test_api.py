import json

from django.contrib.auth.models import User
from django.db.models import F
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username='test_username')
        self.book_1 = Book.objects.create(name='Test book 1', price=100, author='Author1', discount=21,
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='Test book 2', price=200, author='Author1', discount=144)
        self.book_3 = Book.objects.create(name='Test book Author1', price=300, author='Author2')

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            'like': True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                    content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.book_1.refresh_from_db()
        self.assertTrue(relation.like)

    def test_bookmarks(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id, ))
        data = {
            'in_bookmarks': True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertTrue(relation.in_bookmarks)

    def test_rating(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            'rate': 4
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book_1)
        self.assertEqual(4, relation.rate)

    def test_get_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'price': 200})
        books = Book.objects.all().annotate(discount_price=F('price') - F('discount'), owner_name=F('owner__username')). \
            prefetch_related('readers').order_by('id')
        serializer_data = BooksSerializer(books.filter(price=200), many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        books = Book.objects.all().annotate(discount_price=F('price') - F('discount'), owner_name=F('owner__username')).\
                                            prefetch_related('readers').order_by('id')
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author2'})
        serializer_data = BooksSerializer(books.filter(author='Author2'), many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': '-price'})
        books = Book.objects.all().annotate(discount_price=F('price') - F('discount'), owner_name=F('owner__username')). \
            prefetch_related('readers').order_by('-price')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_list(self):
        # URL для одной книги -> book-detail, тк на этом урле висит ViewSet
        url = reverse('book-list')
        response = self.client.get(url)
        books = Book.objects.all().annotate(discount_price=F('price') - F('discount'), owner_name=F('owner__username')). \
            prefetch_related('readers').order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        url = reverse('book-list')

        data = {
            'name': 'Test book 3',
            'price': 890,
            'author': 'Author Name',
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data,
                                    content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(4, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 890,
            'author': self.book_1.author,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.book_1.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(890, self.book_1.price)

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test-username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 890,
            'author': self.book_1.author,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        # print(response.data)
        self.assertEqual({'detail': ErrorDetail(string='You do not have permission to perform this action.', \
                                                code='permission_denied')}, response.data)
        self.book_1.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        # self.assertEqual(890, self.book_1.price)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test-username2', is_staff=True)
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            'name': self.book_1.name,
            'price': 890,
            'author': self.book_1.author,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')
        self.book_1.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(890, self.book_1.price)

    def test_delete(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        data = {
            'name': self.book_1.name,
            'price': self.book_1.price,
            'author': self.book_1.author,
        }
        json_data = json.dumps(data)
        response = self.client.delete(url, data=json_data,
                                      content_type='application/json')
        # self.book_1.refresh_from_db()
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(2, Book.objects.all().count())

    def test_get(self):
        books = Book.objects.all().annotate(discount_price=F('price') - F('discount'), owner_name=F('owner__username')).\
                                            prefetch_related('readers')
        book = books.get(name='Test book 1')
        url = reverse('book-detail', args=(book.id, ))
        response = self.client.get(url)
        serializer_data = BooksSerializer(book).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
