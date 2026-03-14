import sqlite3

conn = sqlite3.connect('findit.db')
c = conn.cursor()

print('Users:')
for row in c.execute('select id, username, email, role from users'):
    print(row)

print('\nItems:')
for row in c.execute('select id, user_id, name, item_type, image_path from items'):
    print(row)

print('\nMatches:')
for row in c.execute('select id, lost_item_id, found_item_id, status, image_similarity_type from matches'):
    print(row)

conn.close()
