# Source - https://stackoverflow.com/q
# Posted by yang xue, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-21, License - CC BY-SA 4.0

import pygame
import pygame.freetype

pygame.init()

pygame.display.set_caption('hello world')

screen = pygame.display.set_mode((800, 600), 0, 32)


ft_font = pygame.freetype.Font("Montserrat-BlackItalic.ttf", 24)
title_surf, title_rect = ft_font.render_to(screen, (100, 100), 'Hello Gamers', (100, 0, 0))


running = True

while running: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        
    screen.fill((25, 25, 25))
    screen.blit(title_surf, title_rect)
    pygame.display.update()

pygame.quit()
