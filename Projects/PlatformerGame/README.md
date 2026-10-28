# Rocket 2025 Internship Game

An endless side-scrolling platformer I wrote in Python with Pygame during my 2025 Rocket internship, featuring pixel art I designed in Piskel.

## How to play

Jump across moving platforms while dodging falling rocks, stars, and traps. Your score goes up the longer you survive, and the game gets harder as it rises.

| Key | Action |
| --- | --- |
| Left / Right arrows | Move |
| Space | Jump |
| 1 to 4 | Switch character |
| P | Pause |
| R | Restart after game over |

- **Trap platforms** slowly drain your health while you stand on them.
- **Heart** pickups restore health. **Trophy** pickups make you immune to damage for 6.5 seconds.
- **Inverted Mode:** between 1,500 and 3,000 points, the whole screen spins 180° and the world plays upside down.
- Your best score is saved to `high_score.txt` between runs.

## Running it

Requires Python 3 and Pygame:

```
pip install pygame
python endgame.py
```

Run it from this folder so the game can find its images.

## How it works

- **Procedural level generation:** platforms are generated in batches ahead of the player and removed once they are off screen behind them. Gaps and height changes are limited to what a full jump can cover, including the case where two neighboring moving platforms drift apart.
- **Physics and collision:** gravity and jumping use per-frame velocity. Landing only counts when the player was above the platform on the previous frame, so you can't snap onto a platform from the side or from below. The player rides along with moving platforms.
- **Scrolling camera:** the camera follows the player, and the background scrolls at half speed for a parallax effect.
- **Difficulty scaling:** falling objects spawn more often and fall faster as the score increases.
- **Screen rotation:** the world is drawn to an off-screen surface first. In Inverted Mode that surface is rotated onto the window, animating smoothly into and out of the flip.

## Art credits

My own pixel art, made in Piskel:

- Three of the playable characters: Breyona (1), Zahia (3), and Jeremiah (4)
- The falling star hazard (`Trap2.png`)
- A two-frame rock monster obstacle (shown on my portfolio; not used in this version of the game)

The hooded character (2), backgrounds, boulder, platform and trap blocks, and the heart and trophy pickup icons are not my own work. The wooden platform tile is from the free Pixel Adventure asset pack by Pixel Frog.
