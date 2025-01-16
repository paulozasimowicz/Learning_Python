# Strings
print('HGvweonvwrjnK'.upper())
print('HGvweonvwrjnK'.lower())
print('cap'.capitalize())

item = "smartwatch"
print(item.upper())
print(item) # original string
item2 = item.upper()
print(item2)


print("Bee".find("e"))

#Lenght function: len(): len() stands for length and, when used on lists, it returns the number of items in the list.

movies = ["avatar","Titanic","avengers"]
print(len(movies))

# append() dunction: The append() function adds a new item to the end of a list. append() is called using dot notation because it’s specific to lists.

songs = ["Yesterday", "Hello","Believer"]
songs.append("imagine")
print(songs)

# Insert function: The insert() function allows you to add an element to a list, at a specific position.

items = ["book","pencil","fridge"]
items.insert(2,"coisa")
print(items)
print(items[2])