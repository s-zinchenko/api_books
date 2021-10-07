from django.contrib.auth.models import User
from django.db.models import F
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):

    def test_ok(self):
        user1 = User.objects.create(username='user1')
        user2 = User.objects.create(username='user2')
        user3 = User.objects.create(username='user3')

        book_1 = Book.objects.create(name='Test book 1', price=54, discount=21, author='Author1', owner=user1)
        book_2 = Book.objects.create(name='Test book 2', price=72, discount=None, author='Author2', owner=user1)

        UserBookRelation.objects.create(user=user1, book=book_1, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True, rate=5)
        user_book_3 = UserBookRelation.objects.create(user=user3, book=book_1, like=True)
        user_book_3.rate = 4
        user_book_3.save()


        UserBookRelation.objects.create(user=user1, book=book_2, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book_2, like=False, rate=4)
        UserBookRelation.objects.create(user=user3, book=book_2, like=True, rate=4)

        # books = Book.objects.filter(discount__isnull=False).annotate(discount_price=)
        books = Book.objects.all().annotate(discount_price=F('price') - F('discount')).order_by('id')

        data = BooksSerializer(books, many=True).data

        expected_data = [
            {
                'name': 'Test book 1',
                'price': '54.00',
                'discount': '21.00',
                'author': 'Author1',
                'discount_price': '33.00',
                'readers': [
                    {
                        'first_name': '',
                        'last_name': '',
                    },
                    {
                        'first_name': '',
                        'last_name': ''
                    },
                    {
                        'first_name': '',
                        'last_name': ''
                    },
                ]

            },
            {
                'name': 'Test book 2',
                'price': '72.00',
                'discount': None,
                'author': 'Author2',
                'discount_price': None,
                'readers': [
                    {
                        'first_name': '',
                        'last_name': '',
                    },
                    {
                        'first_name': '',
                        'last_name': ''
                    },
                    {
                        'first_name': '',
                        'last_name': ''
                    },
                ]

            },
        ]
        print('\n', expected_data, '\n\n', data, '\n')
        self.assertEqual(expected_data, data)
