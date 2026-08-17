import os

old_path = 'app/database/migrations/014_pgvector.sql'
new_path = 'app/database/migrations/014_pgvector_postgres.sql'

if os.path.exists(old_path):
    if os.path.exists(new_path):
        os.remove(new_path)
    os.rename(old_path, new_path)
    print(f'Renamed {old_path} to {new_path}')
else:
    print(f'{old_path} already renamed or does not exist')