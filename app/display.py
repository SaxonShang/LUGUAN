import cv2
import pygame

def display_image(image_path):
    """Displays the AI-generated image on an LED screen."""
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    image = pygame.image.load(image_path)
    screen.blit(image, (0, 0))
    pygame.display.flip()

    # Keep display open for a few seconds
    pygame.time.wait(5000)
    pygame.quit()
