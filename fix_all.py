content = open('src/edysiem/persistence/repository.py', encoding='utf-8').read()
content = content.replace('__all__ = ["BaseRepository", "GenericRepository", "Repository"]', '__all__ = ["GenericRepository", "Repository"]')
open('src/edysiem/persistence/repository.py', 'w', encoding='utf-8').write(content)
print('fixed __all__')