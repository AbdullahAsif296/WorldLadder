# Word Ladder Game

A Python implementation of the classic Word Ladder puzzle game with AI-powered hints and graph visualization.

## Overview

Word Ladder is a word puzzle where players transform one word into another by changing one letter at a time. This implementation features multiple difficulty levels, AI-powered hints using search algorithms (A\*, Greedy, UCS), and interactive graph visualization of word connections.

## Features

- **Multiple Difficulty Modes**

  - Beginner: Shorter words (3-4 letters) with simpler transformations
  - Advanced: Medium-length words (5-6 letters) with more complex paths
  - Challenge: Longer words (6-8 letters), time constraints, and restricted words

- **AI-Powered Assistance**

  - Intelligent hint system using advanced search algorithms
  - Path optimization with multiple search strategies
  - Word validation using NLTK dictionary

- **Interactive Experience**
  - User-friendly GUI built with Pygame
  - Real-time score tracking and timer
  - Interactive graph visualization of word connections
  - Detailed performance analytics

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/word-ladder-game.git
   cd word-ladder-game
   ```

2. Install required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the game:
   ```bash
   python word_ladder_gui.py
   ```

## Gameplay Instructions

1. Select your preferred difficulty level
2. Enter a starting word or use the suggested word pair
3. Transform the start word into the target word by changing one letter at a time
4. Use hints strategically (limited based on difficulty)
5. Complete the transformation in as few steps as possible
6. Review your performance and solution path at the end

## Technical Implementation

### Search Algorithms

The game implements three different search algorithms for finding optimal paths:

- **A\* Search**: Combines path cost and heuristic evaluation for optimal solutions
- **Greedy Best-First Search**: Prioritizes heuristic values for faster but potentially suboptimal solutions
- **Uniform Cost Search**: Focuses solely on path cost, guaranteeing optimality at the expense of efficiency

### Heuristic Function

The game employs a letter-position heuristic:

- Each letter contributes its alphabetical position value (A=1, B=2, ..., Z=26)
- For example, "cat" has a heuristic value of C(3) + A(1) + T(20) = 24
- This approach provides an effective evaluation metric for word transformations

### Graph Visualization

The interactive graph visualization component offers:

- Network representation of word connections
- Color-coded paths for different algorithms
- Node information including heuristic values
- Zoom, pan, and selection capabilities

#### Visualization Controls

- Click: Select nodes for detailed information
- Drag: Reposition the graph
- Scroll: Zoom in/out
- ESC: Return to the game summary screen

### Scoring System

Performance evaluation is based on multiple factors:

- **Base Score**: Determined by difficulty level
- **Optimality Bonus**: Rewards finding optimal or near-optimal paths
- **Time Efficiency**: Faster solutions earn higher scores
- **Move Economy**: Fewer moves result in higher scores
- **Hint Usage**: Strategic use of hints (or lack thereof) affects final score

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Lewis Carroll for inventing the original Word Ladder concept
- NLTK project for providing comprehensive word dictionaries
- Pygame community for the graphics framework
