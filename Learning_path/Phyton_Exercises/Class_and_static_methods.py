# Class methods are called on the class itself, not on individual
#  instances. This allows their use without needing to create a 
# class instance. They are especially useful for actions relevant
#  to the class as a whole, rather than actions limited to a single
#  object. Here's an example:

class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author

    #regular method
    def describe_book(self):
        print(self.title, 'by', self.author)

    # class method
    @classmethod
    def books_in_series(cls, series_name, number_of_books):
        print('There are', number_of_books, 'books in the', series_name, 'series')

# Creating an instance of Book
my_book =  Book("Harry Potter and the Sorceres's Stone", "J.K. Rowlin")

# Using the instance method to describe the book
my_book.describe_book()

# Using the class method to display information about the series
Book.books_in_series("Harry Potter",7)

# Class methods are created using the @classmethod decorator and take the cls argument,
#  which refers to the class itself.

#Instances share everything that a class has, including the class methods.
#  This means that you call a class method on instances as well.

#  Static methods are similar to class methods, except they don't receive any additional arguments; they are identical to normal functions that belong to a class.
# They are marked with the @staticmethod decorator.

# staticmethod
    #@staticmethod
    #def books_in_series(serie_name, number_of_books):
        #print('There are', number_of_books, 'books in the', series_name, 'series')
