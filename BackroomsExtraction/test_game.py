import pygame
import sys
import logging
from settings import *
from game_state import GameState
from player import Player
from enemy import Enemy
from environment import Environment

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='test_game.log'
)

def test_initialization():
    """Test basic initialization of game components"""
    try:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Backrooms Extraction - Test")
        
        # Test Environment
        logging.info("Testing environment generation...")
        env = Environment()
        assert len(env.rooms) > 0, "No rooms generated"
        assert len(env.extraction_points) > 0, "No extraction points generated"
        logging.info("Environment test passed")
        
        # Test Player
        logging.info("Testing player initialization...")
        player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        assert player.health == PLAYER_HEALTH, "Player health not initialized correctly"
        assert player.is_alive(), "Player should be alive at start"
        logging.info("Player test passed")
        
        # Test Enemy
        logging.info("Testing enemy initialization...")
        enemy = Enemy(100, 100)
        assert enemy.current_state == enemy.PATROL, "Enemy should start in patrol state"
        logging.info("Enemy test passed")
        
        # Test Game State
        logging.info("Testing game state...")
        game_state = GameState()
        assert not game_state.game_over, "Game should not be over at start"
        assert not game_state.paused, "Game should not be paused at start"
        logging.info("Game state test passed")
        
        # Visual Test
        logging.info("Running visual test...")
        clock = pygame.time.Clock()
        running = True
        test_duration = FPS * 5  # 5 seconds
        frame_count = 0
        
        while running and frame_count < test_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Clear screen
            screen.fill(BLACK)
            
            # Draw environment
            env.draw(screen, (0, 0))
            
            # Draw player
            player.draw(screen)
            
            # Draw enemy
            enemy.update(player.get_position(), player.get_noise_level())
            enemy.draw(screen)
            
            pygame.display.flip()
            clock.tick(FPS)
            frame_count += 1
            
        logging.info("Visual test completed")
        
        pygame.quit()
        return True
        
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        pygame.quit()
        return False

def run_all_tests():
    """Run all game tests"""
    try:
        logging.info("Starting game tests...")
        
        # Run initialization test
        init_result = test_initialization()
        if init_result:
            logging.info("All tests passed successfully!")
            print("✅ All tests passed! Check test_game.log for details.")
        else:
            logging.error("Tests failed!")
            print("❌ Tests failed! Check test_game.log for details.")
            
    except Exception as e:
        logging.error(f"Test suite failed: {str(e)}")
        print("❌ Test suite failed! Check test_game.log for details.")

if __name__ == "__main__":
    run_all_tests()
