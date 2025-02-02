import cv2
import pygame
import os
import time

def display_image(image_path, screen_size=(640, 480)):
    """
    Displays the AI-generated image on an LED screen using Pygame.
    
    Args:
        image_path (str): Path to the image file.
        screen_size (tuple): Resolution of the display screen (default: 640x480).
    """
    if not os.path.exists(image_path):
        print(f"❌ Error: Image not found at {image_path}")
        return
    
    pygame.init()
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("AI Processed Image")

    try:
        image = pygame.image.load(image_path)

        # ✅ Resize Image to Fit Screen
        image = pygame.transform.scale(image, screen_size)

        screen.blit(image, (0, 0))
        pygame.display.flip()

        print(f"🖼️ Displaying image: {image_path}")

        # ✅ Keep the display open but allow exit with keypress
        running = True
        start_time = time.time()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or time.time() - start_time > 10:  # Closes after 10 seconds
                    running = False
                    break

        pygame.quit()
        print("✅ Display closed.")

    except Exception as e:
        print(f"❌ Error displaying image: {e}")
        pygame.quit()

# ✅ Example Usage (for Testing)
if __name__ == "__main__":
    test_image = "test.jpg"  # Replace with a valid image path
    display_image(test_image)
